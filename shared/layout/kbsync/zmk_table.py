"""Build the ZMK keycode table (name -> HID usage value) from ZMK's dt-bindings headers.

The result is committed as kbsync/data/zmk_keys.json so nothing at runtime needs a ZMK checkout.
"""

import json
import re
from pathlib import Path

from .expr import evaluate

HEADERS = ['hid_usage_pages.h', 'hid_usage.h', 'modifiers.h', 'keys.h']
_DEFINE = re.compile(r'^#define\s+(\w+)\s+(.+?)\s*(//.*)?$', re.M)  # object-like macros only


def build(include_dir):
    include_dir = Path(include_dir)
    defs, deprecated, keys_h = {}, set(), set()
    for name in HEADERS:
        text = re.sub(r'\\\n\s*', ' ', (include_dir / name).read_text())
        for m in _DEFINE.finditer(text):
            defs[m.group(1)] = m.group(2)
            if m.group(3) and 'DEPRECATED' in m.group(3):
                deprecated.add(m.group(1))
            if name == 'keys.h':
                keys_h.add(m.group(1))

    values = {}

    def resolve(name, depth=0):
        if name not in values:
            if name not in defs or depth > 40:
                raise KeyError(name)
            values[name] = evaluate(defs[name], lambda n: resolve(n, depth + 1))
        return values[name]

    for name in defs:
        try:
            resolve(name)
        except (KeyError, ValueError):
            pass
    return {
        'values': dict(sorted(values.items())),
        'deprecated': sorted(deprecated & values.keys()),
        'keys_h': sorted(keys_h & values.keys()),
    }


def write(include_dir, out_path):
    Path(out_path).write_text(json.dumps(build(include_dir), indent=1) + '\n')
