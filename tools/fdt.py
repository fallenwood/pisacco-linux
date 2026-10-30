# SPDX-License-Identifier: GPL-2.0-only
"""Small read-only FDT-v17 / Android DTBO-v0 inspection helpers.

Overlay application is deliberately left to libfdt's fdtoverlay, not implemented
here. These helpers validate bounds and inspect properties without interpreting
vendor drivers or treating static DT data as a live RAM map.
"""
import struct

FDT_MAGIC = 0xd00dfeed
DTBO_MAGIC = 0xd7b7ab1e


def header(blob):
    if len(blob) < 40:
        raise ValueError('truncated FDT header')
    h = struct.unpack_from('>10I', blob)
    if h[0] != FDT_MAGIC or not 40 <= h[1] <= len(blob) or h[5] != 17 or h[6] > 17:
        raise ValueError('invalid or unsupported FDT header')
    if (h[2] < 40 or h[2] % 4 or h[3] < 40 or h[4] < 40 or h[4] % 8 or
            h[4] + 16 > h[1] or h[2] + h[9] > h[1] or h[3] + h[8] > h[1]):
        raise ValueError('FDT block bounds/alignment invalid')
    return h


def split_fdts(blob):
    result = []
    offset = 0
    while offset < len(blob) and any(blob[offset:]):
        h = header(blob[offset:])
        result.append(blob[offset:offset + h[1]])
        offset += h[1]
    if not result:
        raise ValueError('no FDTs')
    return result


def nodes(blob):
    h = header(blob)
    pos, end = h[2], h[2] + h[9]
    strings = blob[h[3]:h[3] + h[8]]
    stack, result = [], {}
    while pos + 4 <= end:
        token = struct.unpack_from('>I', blob, pos)[0]
        pos += 4
        if token == 1:  # FDT_BEGIN_NODE
            nul = blob.find(b'\0', pos, end)
            if nul < 0 or len(stack) >= 256:
                raise ValueError('invalid FDT node name/depth')
            name = blob[pos:nul].decode('utf-8')
            if '/' in name or (not stack and (name or result)):
                raise ValueError('invalid/duplicate FDT root')
            stack.append(name)
            path = '/' + '/'.join(stack[1:])
            if path in result:
                raise ValueError('duplicate FDT node')
            result[path] = {}
            pos = (nul + 4) & ~3
        elif token == 2:  # FDT_END_NODE
            if not stack:
                raise ValueError('unbalanced FDT node')
            stack.pop()
        elif token == 3:  # FDT_PROP
            if not stack or pos + 8 > end:
                raise ValueError('invalid FDT property position')
            size, nameoff = struct.unpack_from('>II', blob, pos)
            pos += 8
            nul = strings.find(b'\0', nameoff)
            if nul < 0 or pos + size > end:
                raise ValueError('invalid FDT property bounds')
            name = strings[nameoff:nul].decode('utf-8')
            props = result['/' + '/'.join(stack[1:])]
            if name in props:
                raise ValueError('duplicate FDT property')
            props[name] = blob[pos:pos + size]
            pos = (pos + size + 3) & ~3
        elif token == 4:  # FDT_NOP
            continue
        elif token == 9:  # FDT_END
            if stack or '/' not in result:
                raise ValueError('unbalanced/missing FDT root')
            return result
        else:
            raise ValueError('unknown FDT token')
    raise ValueError('missing FDT_END')


def dtbo_entries(blob):
    if len(blob) < 32:
        raise ValueError('truncated DTBO table')
    magic, size, hsize, esize, count, offset, page, version = struct.unpack_from('>8I', blob)
    if (magic != DTBO_MAGIC or version != 0 or not 32 <= hsize <= size <= len(blob) or
            esize < 32 or not 1 <= count <= 4096 or offset < hsize or
            offset + count * esize > size or not page or page & (page - 1)):
        raise ValueError('invalid/unsupported DTBO table')
    entries = []
    for index in range(count):
        e = struct.unpack_from('>8I', blob, offset + esize * index)
        dt_size, dt_offset = e[:2]
        if dt_offset < offset + count * esize or dt_size < 40 or dt_offset + dt_size > size:
            raise ValueError('DTBO entry outside table data')
        data = blob[dt_offset:dt_offset + dt_size]
        if header(data)[1] != dt_size:
            raise ValueError('DTBO entry size differs from FDT size')
        entries.append({'index': index, 'size': dt_size, 'offset': dt_offset,
                        'id': e[2], 'rev': e[3], 'custom': list(e[4:]), 'data': data})
    return entries


def fixed_regions(tree):
    parent = tree.get('/reserved-memory', {})
    if not parent:
        return []
    if parent.get('#address-cells') != b'\0\0\0\2' or parent.get('#size-cells') != b'\0\0\0\2':
        raise ValueError('expected 64-bit reserved-memory cells')
    result = []
    for path, props in tree.items():
        if path.startswith('/reserved-memory/') and path.count('/') == 2 and 'reg' in props:
            raw = props['reg']
            if len(raw) % 16:
                raise ValueError('invalid reserved-memory reg')
            for address, size in struct.iter_unpack('>QQ', raw):
                if size:
                    result.append({'node': path, 'start': address, 'size': size, 'no_map': 'no-map' in props})
    return result


def region_covered(required, available):
    pos, end = required['start'], required['start'] + required['size']
    eligible = [r for r in available if not required['no_map'] or r['no_map']]
    for region in sorted(eligible, key=lambda r: r['start']):
        if region['start'] > pos:
            break
        pos = max(pos, region['start'] + region['size'])
        if pos >= end:
            return True
    return False
