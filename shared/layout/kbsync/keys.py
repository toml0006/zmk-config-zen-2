"""Canonical, firmware-neutral key vocabulary.

A binding is a string:
  plain / modified key   a, n1, lbkt, cmd+shift+lbkt, consumer(0x71), usage(0x7002f)
  layers                 mo(number), tog(symbol), to(base), sl(number), lt(number, spc)
  mod-tap                mt(lctrl, z)
  wireless / tooling     bt_sel(0), bt_disc(1), bt_clr, bt_clr_all, bt_nxt, bt_prv, studio_unlock
  pass-through           trans, none
  raw QMK keycode        qmk(0x7c00)   (board profiles for QMK/Vial boards only)

Key names are ZMK's non-deprecated aliases, lowercased, shortest wins (ties alphabetical).
Values are ZMK HID usages: mods << 24 | page << 16 | id.
"""

import json
import re
from functools import cache
from importlib.resources import files

# macOS order: ⌃ ⌥ ⇧ ⌘
MODS = [('ctrl', 0x01), ('alt', 0x04), ('shift', 0x02), ('cmd', 0x08),
        ('rctrl', 0x10), ('ralt', 0x40), ('rshift', 0x20), ('rcmd', 0x80)]
MOD_BIT = dict(MODS)
CONSUMER_PAGE = 0x0C

NULLARY = {'trans', 'none', 'studio_unlock', 'bt_clr', 'bt_clr_all', 'bt_nxt', 'bt_prv'}
CALLS = {'mo', 'tog', 'to', 'sl', 'lt', 'mt', 'bt_sel', 'bt_disc', 'qmk'}
_CALL = re.compile(r'^(\w+)\((.*)\)$')
_RAW = re.compile(r'^(consumer|usage)\((0x[0-9a-fA-F]+)\)$')


@cache
def table():
    data = json.loads(files('kbsync').joinpath('data/zmk_keys.json').read_text())
    values, deprecated = data['values'], set(data['deprecated'])
    by_name, preferred = {}, {}
    for name in data['keys_h']:  # sorted, so strict '<' keeps the alphabetical winner on ties
        v = values[name]
        by_name[name.lower()] = v
        if name not in deprecated and (v not in preferred or len(name) < len(preferred[v])):
            preferred[v] = name
    return values, by_name, preferred


def usage_to_name(v):
    _, _, preferred = table()
    if v in preferred:
        return preferred[v].lower()
    mods, base = v >> 24, v & 0xFFFFFF
    if base in preferred:
        name = preferred[base].lower()
    elif base >> 16 == CONSUMER_PAGE:
        name = f'consumer(0x{base & 0xFFFF:02x})'
    else:
        name = f'usage(0x{base:x})'
    return '+'.join([m for m, bit in MODS if mods & bit] + [name])


def name_to_usage(s):
    _, by_name, _ = table()
    *mods, base = s.strip().lower().split('+')
    if m := _RAW.match(base):
        v = int(m.group(2), 16) | (CONSUMER_PAGE << 16 if m.group(1) == 'consumer' else 0)
    elif base in by_name:
        v = by_name[base]
    else:
        raise ValueError(f'unknown key {base!r} in {s!r}')
    for mod in mods:
        if mod not in MOD_BIT:
            raise ValueError(f'unknown modifier {mod!r} in {s!r}')
        v |= MOD_BIT[mod] << 24
    return v


def parse_binding(s):
    """Return (kind, args) for a canonical binding string."""
    s = s.strip()
    if s in NULLARY:
        return s, ()
    m = _CALL.match(s)
    if m and m.group(1) in CALLS:
        args = tuple(a.strip() for a in m.group(2).split(','))
        if m.group(1) == 'qmk':
            int(args[0], 0)  # validate
        return m.group(1), args
    name_to_usage(s)  # validate
    return 'kp', (s,)


def normalize(s):
    """Canonical spelling of a binding (e.g. 'LS(N1)' style aliases -> preferred names)."""
    kind, args = parse_binding(s)
    if kind == 'kp':
        return usage_to_name(name_to_usage(args[0]))
    if kind == 'mt':
        return f'mt({usage_to_name(name_to_usage(args[0]))}, {usage_to_name(name_to_usage(args[1]))})'
    if kind == 'lt':
        return f'lt({args[0]}, {usage_to_name(name_to_usage(args[1]))})'
    if kind == 'qmk':
        return f'qmk(0x{int(args[0], 0):04x})'
    return s if not args else f'{kind}({", ".join(args)})'
