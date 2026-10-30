#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Read-only split nl80211 GET_WIPHY channel evidence, including INDOOR_ONLY.
No SET commands, scans, device creation, module load or RF lifecycle changes.
This collector is NOT integrated into the installed CN service yet.
Constants verified against project's exact Linux6.18.58 UAPI, not iw text.
"""
import argparse
import json
import os
import socket
import struct
import time

CMD_GET_WIPHY=1
CMD_NEW_WIPHY=3
CMD_GET_PROTOCOL_FEATURES=95
ATTR_WIPHY=1
ATTR_WIPHY_NAME=2
ATTR_WIPHY_BANDS=22
ATTR_SPLIT_WIPHY_DUMP=174
ATTR_PROTOCOL_FEATURES=173
BAND_ATTR_FREQS=1
FREQ_ATTR_FREQ=1
FREQ_ATTR_DISABLED=2
FREQ_ATTR_NO_IR=3
FREQ_ATTR_RADAR=5
FREQ_ATTR_MAX_TX_POWER=6
FREQ_ATTR_INDOOR_ONLY=14
FREQ_ATTR_NO_20MHZ=16
FREQ_ATTR_OFFSET=20
SPLIT_FEATURE=1


def require(ok,message):
    if not ok:raise ValueError(message)


def aligned(n):return (n+3)&~3


def attribute(kind,payload=b''):
    data=struct.pack('=HH',4+len(payload),kind)+payload
    return data+bytes(aligned(len(data))-len(data))


def attributes(data):
    out={};pos=0
    while pos<len(data):
        require(len(data)-pos>=4,'Truncated attribute header')
        length,kind=struct.unpack_from('=HH',data,pos)
        require(length>=4 and pos+length<=len(data),'Attribute exceeds message')
        key=kind&0x3fff
        require(key not in out,'Duplicate attribute type')
        out[key]=data[pos+4:pos+length]
        step=aligned(length)
        require(pos+step<=len(data),'Attribute padding exceeds message')
        require(not any(data[pos+length:pos+step]),'Nonzero attribute padding')
        pos+=step
    return out


def u32(data):
    require(len(data)==4,'Expected u32 attribute')
    return struct.unpack('=I',data)[0]


def flag(attrs,key):
    if key not in attrs:return False
    require(attrs[key]==b'','Flag has unexpected payload')
    return True


def decode_frequency(data):
    a=attributes(data);require(FREQ_ATTR_FREQ in a,'Channel without frequency')
    frequency=u32(a[FREQ_ATTR_FREQ]);offset=u32(a[FREQ_ATTR_OFFSET]) if FREQ_ATTR_OFFSET in a else 0
    require(0<frequency<100000 and offset<1000,'Invalid frequency/offset')
    disabled=flag(a,FREQ_ATTR_DISABLED)
    power=u32(a[FREQ_ATTR_MAX_TX_POWER]) if FREQ_ATTR_MAX_TX_POWER in a else None
    require(disabled or power is not None,'Enabled channel without actual power')
    return {'frequency_mhz':frequency+offset/1000,'disabled':disabled,'max_tx_power_mbm':power,
        'no_ir':flag(a,FREQ_ATTR_NO_IR),'radar':flag(a,FREQ_ATTR_RADAR),'indoor_only':flag(a,FREQ_ATTR_INDOOR_ONLY),
        'no_20mhz':flag(a,FREQ_ATTR_NO_20MHZ),'observed_attribute_ids':sorted(a)}


def merge_wiphy(phys,payload):
    require(len(payload)>=4 and payload[0]==CMD_NEW_WIPHY,'Unexpected wiphy response command')
    a=attributes(payload[4:]);require(ATTR_WIPHY in a,'Response without PHY identity');index=u32(a[ATTR_WIPHY])
    phy=phys.setdefault(index,{'index':index,'name':None,'channels':{}})
    if ATTR_WIPHY_NAME in a:
        raw=a[ATTR_WIPHY_NAME];require(raw.endswith(b'\0') and b'\0' not in raw[:-1],'Invalid PHY name')
        name=raw[:-1].decode('ascii');require(phy['name'] in (None,name),'PHY name changed within dump');phy['name']=name
    for band_id,band in attributes(a.get(ATTR_WIPHY_BANDS,b'')).items():
        b=attributes(band)
        for entry in attributes(b.get(BAND_ATTR_FREQS,b'')).values():
            value=decode_frequency(entry);value['band_index']=band_id;key=(band_id,value['frequency_mhz'])
            require(key not in phy['channels'] or phy['channels'][key]==value,'Channel changed within split dump')
            phy['channels'][key]=value


class ReadOnlyNetlink:
    def __init__(self):
        self.sock=socket.socket(socket.AF_NETLINK,socket.SOCK_RAW,16)
        self.sock.bind((0,0));self.port=self.sock.getsockname()[0];self.sequence=time.monotonic_ns()&0xffffffff
        self.deadline=time.monotonic()+8;self.bytes=0;self.messages=0;self.family=None

    def close(self):self.sock.close()

    def exchange(self,family,command,attrs=b'',dump=False,version=1):
        require((family==16 and command==3 and self.family is None and not dump) or
            (family==self.family and command==CMD_GET_PROTOCOL_FEATURES and not dump) or
            (family==self.family and command==CMD_GET_WIPHY and dump),'Only fixed GET requests permitted')
        self.sequence=(self.sequence+1)&0xffffffff;sequence=self.sequence
        body=struct.pack('=BBH',command,version,0)+attrs
        flags=1|(0x300 if dump else 0)
        packet=struct.pack('=IHHII',16+len(body),family,flags,sequence,self.port)+body
        self.sock.sendto(packet,(0,0));replies=[]
        while True:
            remaining=self.deadline-time.monotonic();require(remaining>0,'Read-only netlink deadline')
            self.sock.settimeout(remaining)
            data,ancillary,msg_flags,address=self.sock.recvmsg(1024*1024)
            require(address[0]==0 and not msg_flags&socket.MSG_TRUNC,'Nonkernel or truncated reply')
            self.bytes+=len(data);require(self.bytes<=4*1024*1024,'Netlink byte budget exceeded')
            pos=0
            while pos<len(data):
                require(len(data)-pos>=16,'Truncated netlink header')
                length,kind,reply_flags,seq,pid=struct.unpack_from('=IHHII',data,pos)
                require(length>=16 and pos+length<=len(data),'Invalid netlink message length')
                payload=data[pos+16:pos+length];pos+=aligned(length);self.messages+=1
                require(self.messages<=2048,'Netlink message budget exceeded')
                require(seq==sequence and pid in (0,self.port),'Unmatched sequence or destination')
                require(not reply_flags&0x10,'Interrupted split dump, no complete evidence')
                if kind==2:
                    require(len(payload)>=4,'Malformed netlink error')
                    error=struct.unpack_from('=i',payload)[0]
                    require(error==0,'Kernel netlink error '+str(error))
                    continue
                if kind==3:
                    require(dump,'Unexpected dump completion')
                    require(not payload or len(payload)>=4 and struct.unpack_from('=i',payload)[0]==0,'Dump completion error')
                    return replies
                require(kind==family,'Wrong generic netlink family');replies.append(payload)
            require(pos==len(data),'Netlink padding exceeds datagram')
            if not dump and replies:return replies

    def collect(self,phy_index=None):
        reply=self.exchange(16,3,attribute(2,b'nl80211\0'),version=2)
        require(len(reply)==1,'Ambiguous nl80211 family')
        attrs=attributes(reply[0][4:]);require(1 in attrs and len(attrs[1])==2,'Missing family ID')
        self.family=struct.unpack('=H',attrs[1])[0]
        require(self.family>16,'Unexpected dynamic family')
        replies=self.exchange(self.family,CMD_GET_PROTOCOL_FEATURES)
        require(len(replies)==1,'Ambiguous protocol features');a=attributes(replies[0][4:])
        require(ATTR_PROTOCOL_FEATURES in a,'Protocol features absent');features=u32(a[ATTR_PROTOCOL_FEATURES])
        require(features&SPLIT_FEATURE,'Split dump unsupported; indoor absence cannot be interpreted')
        request=attribute(ATTR_SPLIT_WIPHY_DUMP)
        if phy_index is not None:request+=attribute(ATTR_WIPHY,struct.pack('=I',phy_index))
        messages=self.exchange(self.family,CMD_GET_WIPHY,request,dump=True);phys={}
        for message in messages:merge_wiphy(phys,message)
        require(phy_index is None or set(phys)=={phy_index},'Requested PHY absent or wrong PHY returned')
        result=[]
        for index,phy in sorted(phys.items()):
            result.append({'index':index,'name':phy['name'],'channels':sorted(phy['channels'].values(),key=lambda c:(c['band_index'],c['frequency_mhz']))})
        return {'source':'read_only_raw_nl80211_split_GET_WIPHY','kernel_release':os.uname().release,
            'protocol_features':features,'split_requested':True,'complete_dump':True,'phys':result,
            'received_bytes':self.bytes,'no_radio_activation_scan_or_configuration_write':True,
            'no_PHYS_does_not_prove_live_indoor_flags':not bool(result)}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--read-only',action='store_true',required=True)
    parser.add_argument('--phy-index',type=int);args=parser.parse_args()
    require(args.phy_index is None or 0<=args.phy_index<2**32,'Invalid PHY index')
    client=ReadOnlyNetlink()
    try:out=client.collect(args.phy_index)
    finally:client.close()
    print(json.dumps(out,indent=2))


if __name__=='__main__':main()
