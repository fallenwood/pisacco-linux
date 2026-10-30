# SPDX-License-Identifier: GPL-2.0-only
import importlib.util
import json
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('wifi_auth_evidence',Path(__file__).resolve().parents[1]/'tools/wifi-auth-evidence.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
PEER='00:11:22:33:44:55'
KEY=f'wlan0: WPA: Key negotiation completed with {PEER} [PTK=CCMP GTK=CCMP]'
CON=f'wlan0: CTRL-EVENT-CONNECTED - Connection to {PEER} completed [id=0 id_str=]'

def rows(*messages):
 return '\n'.join(json.dumps({'__MONOTONIC_TIMESTAMP':str(t*1000000),'MESSAGE':msg}) for t,msg in messages)


class AuthEvidence(unittest.TestCase):
 def test_fresh_rsn_ccmp_connected_without_control_socket(self):
  proof=m.verify_ccmp_handshake(rows((10,KEY),(11,CON)),9,rsn_only=True)
  self.assertTrue(proof['handshake_verified'])
  self.assertFalse(proof['wpa_cli_socket_required'])
  self.assertFalse(proof['secret_properties_read'])
 def test_stale_mismatched_cipher_peer_or_interface_rejected(self):
  for log in (rows((1,KEY),(2,CON)),rows((10,KEY.replace('GTK=CCMP','GTK=TKIP')),(11,CON)),rows((10,KEY),(11,CON.replace(PEER,'00:11:22:33:44:66'))),rows((10,KEY.replace('wlan0','wlan1')),(11,CON))):
   with self.assertRaises(ValueError):m.verify_ccmp_handshake(log,9,rsn_only=True)
 def test_disconnect_invalidates_prior_handshake(self):
  for extra in ([],[(13,CON)]):
   log=rows((10,KEY),(11,CON),(12,'wlan0: CTRL-EVENT-DISCONNECTED bssid='+PEER+' reason=3'),*extra)
   with self.assertRaises(ValueError):m.verify_ccmp_handshake(log,9,rsn_only=True)
 def test_mixed_wpa_profile_or_missing_handshake_not_accepted(self):
  with self.assertRaises(ValueError):m.verify_ccmp_handshake(rows((10,KEY),(11,CON)),9,rsn_only=False)
  with self.assertRaises(ValueError):m.verify_ccmp_handshake(rows((11,CON)),9,rsn_only=True)
  with self.assertRaises(ValueError):m.verify_ccmp_handshake('',9,rsn_only=True)


if __name__=='__main__':unittest.main()
