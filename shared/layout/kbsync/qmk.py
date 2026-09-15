"""QMK codec (Vial protocol 6 / QMK >= 0.19 keycodes): canonical binding -> 16-bit keycode."""

from .keys import name_to_usage, parse_binding

KC_NO, KC_TRNS = 0x0000, 0x0001
QK_MOD_TAP, QK_LAYER_TAP = 0x2000, 0x4000
LAYER_BASE = {'to': 0x5200, 'mo': 0x5220, 'tog': 0x5260, 'sl': 0x5280}

# HID consumer usage -> QMK basic-range keycode
CONSUMER = {
    0xE2: 0xA8, 0xE9: 0xA9, 0xEA: 0xAA,              # mute, vol+, vol-
    0xB5: 0xAB, 0xB6: 0xAC, 0xB7: 0xAD, 0xCD: 0xAE,  # next, prev, stop, play/pause
    0xB3: 0xBB, 0xB4: 0xBC,                          # fast-forward, rewind
    0x6F: 0xBD, 0x70: 0xBE,                          # brightness up / down
}

# modifier key usages E0..E7 -> QMK 5-bit mod (0x10 = right-hand)
MOD_KEY = {0xE0: 0x01, 0xE1: 0x02, 0xE2: 0x04, 0xE3: 0x08, 0xE4: 0x11, 0xE5: 0x12, 0xE6: 0x14, 0xE7: 0x18}


class Unsupported(ValueError):
    """Binding has no QMK equivalent; callers degrade it to KC_NO."""


def _mods5(zmk_mods):
    # ZMK bits: LC 01 LS 02 LA 04 LG 08, RC 10 RS 20 RA 40 RG 80. QMK low nibble matches the left bits.
    if zmk_mods & 0x0F and zmk_mods & 0xF0:
        raise Unsupported('mixed left/right modifiers')
    return (zmk_mods >> 4) | 0x10 if zmk_mods & 0xF0 else zmk_mods


def _basic(usage):
    page, uid = usage >> 16, usage & 0xFFFF
    if page == 0x07 and uid <= 0xFF:
        return uid
    if page == 0x0C and uid in CONSUMER:
        return CONSUMER[uid]
    raise Unsupported(f'no QMK keycode for usage 0x{usage:x}')


def to_qmk(binding, layer_ids):
    kind, args = parse_binding(binding)
    if kind == 'trans':
        return KC_TRNS
    if kind == 'none':
        return KC_NO
    if kind == 'qmk':
        return int(args[0], 0)
    if kind in LAYER_BASE:
        return LAYER_BASE[kind] | layer_ids.index(args[0])
    if kind == 'kp':
        v = name_to_usage(args[0])
        kc, mods = _basic(v & 0xFFFFFF), _mods5(v >> 24)
        return (mods << 8) | kc
    if kind == 'lt':
        v = name_to_usage(args[1])
        if v >> 24:
            raise Unsupported('layer-tap with a modified key')
        return QK_LAYER_TAP | (layer_ids.index(args[0]) << 8) | _basic(v)
    if kind == 'mt':
        mod, key = name_to_usage(args[0]), name_to_usage(args[1])
        if mod & 0xFFFF not in MOD_KEY or key >> 24:
            raise Unsupported(f'mod-tap {binding}')
        return QK_MOD_TAP | (MOD_KEY[mod & 0xFFFF] << 8) | _basic(key)
    raise Unsupported(f'{kind} has no QMK equivalent')


def to_qmk_or_none(binding, layer_ids):
    """(keycode, reason) — reason is set when the binding was degraded to KC_NO."""
    try:
        return to_qmk(binding, layer_ids), None
    except Unsupported as e:
        return KC_NO, str(e)
