# SPDX-License-Identifier: GPL-2.0-only
import contextlib
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
import io
from pathlib import Path
import re
import tempfile
import threading
import unittest
from unittest.mock import patch
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('fetch_stock', ROOT/'tools/fetch-stock-boot.py')
fetch_stock = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fetch_stock)


class RangeFetchTests(unittest.TestCase):
    def setUp(self):
        # Do not send local fixture traffic through the user's HTTP proxy.
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        urlopen_patch = patch('urllib.request.urlopen', new=opener.open)
        urlopen_patch.start()
        self.addCleanup(urlopen_patch.stop)
        self.payload = b'synthetic boot.img\0' * 1000
        archive = io.BytesIO()
        with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
            z.writestr('boot.img', self.payload)
            z.writestr('vendor.data', bytes(100000))
        self.archive = archive.getvalue()
        with zipfile.ZipFile(io.BytesIO(self.archive)) as z:
            self.crc = f'{z.getinfo("boot.img").CRC:08x}'
        self.mode = 'normal'
        fixture = self

        class Handler(BaseHTTPRequestHandler):
            def do_HEAD(self):
                self.send_response(200)
                self.send_header('Content-Length', str(len(fixture.archive)))
                self.send_header('ETag', '"test-archive"')
                self.end_headers()

            def do_GET(self):
                match = re.fullmatch(r'bytes=(\d+)-(\d+)', self.headers.get('Range', ''))
                if fixture.mode == 'ignore-range':
                    self.send_response(200)
                    self.send_header('Content-Length', '0')
                    self.end_headers()
                    return
                if not match:
                    self.send_error(416)
                    return
                start, end = map(int, match.groups())
                body = fixture.archive[start:end + 1]
                self.send_response(206)
                self.send_header('Content-Length', str(len(body)))
                self.send_header('Content-Range', f'bytes {start}-{end}/{len(fixture.archive)}')
                self.send_header('ETag', '"changed"' if fixture.mode == 'changed-etag' else '"test-archive"')
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *args):
                pass

        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.close_server)
        self.url = f'http://127.0.0.1:{self.server.server_port}/firmware.zip'
        self.item = {'archive_url': self.url, 'archive_size': len(self.archive),
                     'member': 'boot.img', 'size': len(self.payload), 'zip_crc32': self.crc,
                     'sha256': hashlib.sha256(self.payload).hexdigest()}

    def close_server(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def test_seek_and_exact_ranges(self):
        with fetch_stock.RangeReader(self.url) as reader:
            reader.seek(-22, io.SEEK_END)
            self.assertEqual(reader.read(4), b'PK\x05\x06')
            reader.seek(0)
            self.assertEqual(reader.read(4), b'PK\x03\x04')
            self.assertEqual(reader.transferred, 8)
            with self.assertRaises(ValueError): reader.seek(-1)

    def test_member_extraction_and_cached_pin(self):
        with tempfile.TemporaryDirectory() as td, contextlib.redirect_stdout(io.StringIO()):
            destination = Path(td)/'stock/boot.img'
            fetch_stock.fetch(self.item, destination)
            self.assertEqual(destination.read_bytes(), self.payload)
            # A cached, verified input does not even need a reachable server.
            fetch_stock.fetch(dict(self.item, archive_url='http://127.0.0.1:1/'), destination)

    def test_ignored_range_rejected(self):
        self.mode = 'ignore-range'
        with fetch_stock.RangeReader(self.url) as reader, self.assertRaisesRegex(ValueError, 'ignored'):
            reader.read(4)

    def test_changed_etag_rejected(self):
        self.mode = 'changed-etag'
        with fetch_stock.RangeReader(self.url) as reader, self.assertRaisesRegex(ValueError, 'ETag'):
            reader.read(4)

    def test_hash_mismatch_cleans_partial_output(self):
        with tempfile.TemporaryDirectory() as td:
            destination = Path(td)/'boot.img'
            with self.assertRaisesRegex(ValueError, 'SHA256'):
                fetch_stock.fetch(dict(self.item, sha256='0'*64), destination)
            self.assertEqual(list(Path(td).iterdir()), [])

    def test_existing_wrong_file_not_overwritten(self):
        with tempfile.TemporaryDirectory() as td:
            destination = Path(td)/'boot.img'
            destination.write_bytes(b'existing')
            with self.assertRaisesRegex(ValueError, 'overwrite'):
                fetch_stock.fetch(self.item, destination)
            self.assertEqual(destination.read_bytes(), b'existing')

    def test_wrong_archive_size_rejected(self):
        with tempfile.TemporaryDirectory() as td, self.assertRaisesRegex(ValueError, 'archive size'):
            fetch_stock.fetch(dict(self.item, archive_size=len(self.archive)+1), Path(td)/'boot.img')

    def test_wrong_crc_metadata_rejected(self):
        with tempfile.TemporaryDirectory() as td, self.assertRaisesRegex(ValueError, 'metadata'):
            fetch_stock.fetch(dict(self.item, zip_crc32='00000000'), Path(td)/'boot.img')


if __name__ == '__main__':
    unittest.main()
