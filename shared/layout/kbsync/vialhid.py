"""VIA/Vial raw-HID client over libhidapi (ctypes; `brew install hidapi`)."""

import ctypes as C
import ctypes.util
import json
import lzma
import struct


def _load():
    for name in (ctypes.util.find_library('hidapi'), '/opt/homebrew/lib/libhidapi.dylib',
                 '/usr/local/lib/libhidapi.dylib', 'libhidapi-hidraw.so.0', 'libhidapi-libusb.so.0'):
        if name:
            try:
                return C.CDLL(name)
            except OSError:
                pass
    raise OSError('libhidapi not found (brew install hidapi)')


class _Info(C.Structure):
    pass


_Info._fields_ = [('path', C.c_char_p), ('vendor_id', C.c_ushort), ('product_id', C.c_ushort),
                  ('serial_number', C.c_wchar_p), ('release_number', C.c_ushort),
                  ('manufacturer_string', C.c_wchar_p), ('product_string', C.c_wchar_p),
                  ('usage_page', C.c_ushort), ('usage', C.c_ushort), ('interface_number', C.c_int),
                  ('next', C.POINTER(_Info))]

_lib = None


def lib():
    global _lib
    if _lib is None:
        _lib = _load()
        _lib.hid_enumerate.restype = C.POINTER(_Info)
        _lib.hid_open_path.restype = C.c_void_p
        _lib.hid_open_path.argtypes = [C.c_char_p]
        _lib.hid_write.argtypes = [C.c_void_p, C.c_char_p, C.c_size_t]
        _lib.hid_read_timeout.argtypes = [C.c_void_p, C.c_char_p, C.c_size_t, C.c_int]
        _lib.hid_close.argtypes = [C.c_void_p]
        _lib.hid_init()
    return _lib


class Vial:
    def __init__(self, vid, pid):
        node, path = lib().hid_enumerate(vid, pid), None
        while node:
            i = node.contents
            if i.usage_page == 0xFF60 and i.usage == 0x61:
                path, self.product = i.path, i.product_string
            node = i.next
        if not path:
            raise IOError(f'no VIA/Vial raw HID interface for {vid:04x}:{pid:04x} — is the board plugged in?')
        self.dev = lib().hid_open_path(path)
        if not self.dev:
            raise IOError('hid_open_path failed')

    def close(self):
        lib().hid_close(self.dev)

    def cmd(self, *data):
        if lib().hid_write(self.dev, b'\0' + bytes(data).ljust(32, b'\0'), 33) < 0:
            raise IOError('hid_write failed')
        buf = C.create_string_buffer(32)
        if lib().hid_read_timeout(self.dev, buf, 32, 1000) <= 0:
            raise IOError('HID read timeout')
        return buf.raw

    # VIA
    def layer_count(self):
        return self.cmd(0x11)[1]

    def keymap(self, rows, cols):
        layers = self.layer_count()
        size, buf = layers * rows * cols * 2, b''
        while len(buf) < size:
            n = min(28, size - len(buf))
            buf += self.cmd(0x12, len(buf) >> 8, len(buf) & 0xFF, n)[4:4 + n]
        k = lambda i: buf[2 * i] << 8 | buf[2 * i + 1]
        return [[[k((l * rows + r) * cols + c) for c in range(cols)] for r in range(rows)] for l in range(layers)]

    def set_key(self, layer, row, col, kc):
        self.cmd(0x05, layer, row, col, kc >> 8, kc & 0xFF)

    # Vial
    def vial_protocol(self):
        return struct.unpack('<I', self.cmd(0xFE, 0x00)[:4])[0]

    def definition(self):
        size = struct.unpack('<I', self.cmd(0xFE, 0x01)[:4])[0]
        blob, page = b'', 0
        while len(blob) < size:
            blob += self.cmd(0xFE, 0x02, *struct.pack('<I', page))
            page += 1
        return json.loads(lzma.decompress(blob[:size]))

    def unlocked(self):
        return bool(self.cmd(0xFE, 0x05)[0])

    def combo_count(self):
        return self.cmd(0xFE, 0x0D, 0x00)[1]

    def combo_get(self, idx):
        return list(struct.unpack('<5H', self.cmd(0xFE, 0x0D, 0x03, idx)[1:11]))

    def combo_set(self, idx, entry):
        if self.cmd(0xFE, 0x0D, 0x04, idx, *struct.pack('<5H', *entry))[0] != 0:
            raise IOError(f'combo_set {idx} rejected')
