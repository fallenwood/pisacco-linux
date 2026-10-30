#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Fetch the hash-pinned boot.img in device.json without downloading vendor data.

zipfile reads a seekable HTTP Range view. All ranges are explicit (some CDNs
reject suffix ranges); responses must be 206 with exact bounds and stable ETag.
ZIP CRC32 and the separately pinned member SHA256 are checked, not a publisher
signature or the hash of the entire archive.
"""
import hashlib
import io
import json
from pathlib import Path
import tempfile
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]


class RangeReader(io.RawIOBase):
    def __init__(self, url):
        super().__init__()
        request = urllib.request.Request(url, method='HEAD', headers={'Accept-Encoding': 'identity'})
        with urllib.request.urlopen(request, timeout=60) as response:
            self.url = response.geturl()
            self.size = int(response.headers['Content-Length'])
            self.etag = response.headers.get('ETag')
        if self.size <= 0:
            raise ValueError('invalid remote archive size')
        self.position = 0
        self.transferred = 0

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.position

    def seek(self, offset, whence=io.SEEK_SET):
        bases = {io.SEEK_SET: 0, io.SEEK_CUR: self.position, io.SEEK_END: self.size}
        if whence not in bases or not 0 <= bases[whence] + offset <= self.size:
            raise ValueError('out-of-bounds ZIP seek')
        self.position = bases[whence] + offset
        return self.position

    def read(self, count=-1):
        count = self.size - self.position if count < 0 else min(count, self.size - self.position)
        if not count:
            return b''
        if count > 64 << 20 or self.transferred + count > 96 << 20:
            raise ValueError('range download exceeds boot-only transfer budget')
        start, end = self.position, self.position + count - 1
        headers = {'Range': f'bytes={start}-{end}', 'Accept-Encoding': 'identity'}
        if self.etag:
            headers['If-Range'] = self.etag
        with urllib.request.urlopen(urllib.request.Request(self.url, headers=headers), timeout=60) as response:
            if response.status != 206 or response.headers.get('Content-Range') != f'bytes {start}-{end}/{self.size}':
                raise ValueError('server ignored or changed the requested byte range')
            if self.etag and response.headers.get('ETag') != self.etag:
                raise ValueError('archive ETag changed during download')
            data = response.read(count + 1)
        if len(data) != count:
            raise ValueError('truncated/oversized HTTP Range response')
        self.position += count
        self.transferred += count
        return data


def sha256(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def fetch(item, destination):
    if destination.exists():
        if destination.stat().st_size != item['size'] or sha256(destination) != item['sha256']:
            raise ValueError(f'{destination}: existing file does not match pin; refusing to overwrite')
        print(f'{destination}: cached SHA256 OK')
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    reader = RangeReader(item['archive_url'])
    if reader.size != item['archive_size']:
        raise ValueError('archive size does not match device.json')
    temporary = None
    try:
        with zipfile.ZipFile(reader) as archive:
            matches = [x for x in archive.infolist() if x.filename == item['member']]
            if len(matches) != 1:
                raise ValueError('missing or ambiguous boot.img ZIP member')
            info = matches[0]
            if (info.file_size != item['size'] or info.file_size > 256 << 20 or
                    info.compress_size > 64 << 20 or info.flag_bits & 1 or
                    f'{info.CRC:08x}' != item['zip_crc32']):
                raise ValueError('ZIP member metadata does not match device.json')
            with archive.open(info) as source, tempfile.NamedTemporaryFile(
                    dir=destination.parent, prefix=destination.name + '.', delete=False) as output:
                temporary = Path(output.name)
                while chunk := source.read(1 << 20):
                    output.write(chunk)
        if temporary.stat().st_size != item['size'] or sha256(temporary) != item['sha256']:
            raise ValueError('boot.img SHA256 mismatch')
        temporary.chmod(0o644)
        temporary.replace(destination)
        print(f'{destination}: ZIP CRC32 + SHA256 OK; fetched {reader.transferred} archive bytes')
    finally:
        reader.close()
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main():
    item = json.loads((ROOT / 'device.json').read_text())['stock_boot']
    fetch(item, ROOT / 'downloads' / item['file'])


if __name__ == '__main__':
    main()
