"""ZMK codec: canonical bindings <-> ZMK Studio triplets <-> .keymap text."""

import re

from .expr import evaluate
from .keys import name_to_usage, parse_binding, table, usage_to_name
from .layout import board_layers

# ZMK Studio behavior display names -> canonical kinds
STUDIO_KINDS = {
    'Key Press': 'kp', 'Momentary Layer': 'mo', 'Toggle Layer': 'tog', 'To Layer': 'to',
    'Sticky Layer': 'sl', 'Layer-Tap': 'lt', 'Mod-Tap': 'mt', 'Transparent': 'trans',
    'None': 'none', 'Bluetooth': 'bt', 'Studio Unlock': 'studio_unlock',
}
BT_CMDS = {'bt_clr': 0, 'bt_nxt': 1, 'bt_prv': 2, 'bt_sel': 3, 'bt_clr_all': 4, 'bt_disc': 5}
BT_WITH_PARAM = {'bt_sel', 'bt_disc'}
_BT_NAME = {v: k for k, v in BT_CMDS.items()}
LAYER_KINDS = {'mo', 'tog', 'to', 'sl'}


# ---------------------------------------------------------------- triplets (kind, param1, param2)

def to_triplet(binding, layer_ids):
    kind, args = parse_binding(binding)
    if kind == 'kp':
        return 'kp', name_to_usage(args[0]), 0
    if kind in LAYER_KINDS:
        return kind, layer_ids.index(args[0]), 0
    if kind == 'lt':
        return 'lt', layer_ids.index(args[0]), name_to_usage(args[1])
    if kind == 'mt':
        return 'mt', name_to_usage(args[0]), name_to_usage(args[1])
    if kind in BT_CMDS:
        return 'bt', BT_CMDS[kind], int(args[0], 0) if args else 0
    if kind == 'qmk':
        raise ValueError(f'{binding} is QMK-only')
    return kind, 0, 0


def from_triplet(kind, p1, p2, layer_ids):
    if kind == 'kp':
        return usage_to_name(p1)
    if kind in LAYER_KINDS:
        return f'{kind}({layer_ids[p1]})'
    if kind == 'lt':
        return f'lt({layer_ids[p1]}, {usage_to_name(p2)})'
    if kind == 'mt':
        return f'mt({usage_to_name(p1)}, {usage_to_name(p2)})'
    if kind == 'bt':
        name = _BT_NAME[p1]
        return f'{name}({p2})' if name in BT_WITH_PARAM else name
    return kind


def from_studio(raw, behaviors, layer_ids):
    """raw = [behavior_id, param1, param2]; behaviors = {id: display name}."""
    bid, p1, p2 = raw
    return from_triplet(STUDIO_KINDS[behaviors[str(bid)]], p1, p2, layer_ids)


# ---------------------------------------------------------------- .keymap text

def zmk_expr(v):
    _, _, preferred = table()
    if v in preferred:
        return preferred[v]
    mods, base = v >> 24, v & 0xFFFFFF
    if base in preferred:
        expr = preferred[base]
    elif base >> 16 == 0x0C:
        expr = f'ZMK_HID_USAGE(HID_USAGE_CONSUMER, 0x{base & 0xFFFF:02X})'
    else:
        expr = f'ZMK_HID_USAGE(0x{base >> 16:02X}, 0x{base & 0xFFFF:02X})'
    for fn, bit in reversed([('LC', 0x01), ('LA', 0x04), ('LS', 0x02), ('LG', 0x08),
                             ('RC', 0x10), ('RA', 0x40), ('RS', 0x20), ('RG', 0x80)]):
        if mods & bit:
            expr = f'{fn}({expr})'
    return expr if re.fullmatch(r'\w+', expr) else f'({expr})'


def to_zmk_text(binding, layer_ids):
    kind, p1, p2 = to_triplet(binding, layer_ids)
    if kind == 'kp':
        return f'&kp {zmk_expr(p1)}'
    if kind in LAYER_KINDS:
        return f'&{kind} {p1}'
    if kind == 'lt':
        return f'&lt {p1} {zmk_expr(p2)}'
    if kind == 'mt':
        return f'&mt {zmk_expr(p1)} {zmk_expr(p2)}'
    if kind == 'bt':
        name = _BT_NAME[p1].upper()
        return f'&bt {name} {p2}' if _BT_NAME[p1] in BT_WITH_PARAM else f'&bt {name}'
    return f'&{kind}'


def _split_args(text):
    out, depth, cur = [], 0, ''
    for ch in text:
        depth += ch == '('
        depth -= ch == ')'
        if ch.isspace() and depth == 0:
            if cur:
                out.append(cur)
            cur = ''
        else:
            cur += ch
    return out + ([cur] if cur else [])


def parse_zmk_binding(text):
    """'&kp LG(LBKT)' (without '&' is fine too) -> (kind, p1, p2)."""
    values, _, _ = table()
    name, *args = _split_args(text.lstrip('&'))

    def val(expr):
        return evaluate(expr, lambda n: values[n])

    if name == 'bt':
        cmd = args[0].lower()
        if cmd not in BT_CMDS:
            raise ValueError(f'unknown bt command {args[0]}')
        return 'bt', BT_CMDS[cmd], val(args[1]) if len(args) > 1 else 0
    params = [val(a) for a in args] + [0, 0]
    return name, params[0], params[1]


def _strip_comments(text):
    return re.sub(r'//[^\n]*', '', re.sub(r'/\*.*?\*/', '', text, flags=re.S))


_LAYER = re.compile(r'(\w+)\s*\{\s*display-name\s*=\s*"([^"]*)";(.*?)bindings\s*=\s*<(.*?)>;', re.S)


def parse_keymap(text):
    """Layers from a .keymap: [{node, name, reserved, bindings: [(kind, p1, p2)]}]."""
    text = _strip_comments(text)
    body = text[text.index('zmk,keymap'):]
    return [{
        'node': m.group(1), 'name': m.group(2), 'reserved': 'reserved' in m.group(3),
        'bindings': [parse_zmk_binding(b) for b in m.group(4).split('&') if b.strip()],
    } for m in _LAYER.finditer(body)]


def generate_keymap(base, profile):
    zmk = profile.get('zmk', {})
    layers = board_layers(base, profile)
    ids = [l['id'] for l in layers]
    positions = profile['positions']
    row_lens = profile.get('row_lengths') or [len(positions)]
    uses_mt = any(parse_binding(b)[0] == 'mt' for l in layers for b in l['bindings'])
    timing = base.get('timing', {})

    out = [
        '/*',
        f" * GENERATED by kbsync from shared/layout/base.yaml + boards/{profile['board']}.yaml.",
        f" * Layout: {base['name']}. Edit those files and run `kbsync gen {profile['board']}`;",
        ' * hand edits here are overwritten.',
        ' */',
        '',
        '#include <behaviors.dtsi>',
        '#include <dt-bindings/zmk/keys.h>',
        '#include <dt-bindings/zmk/bt.h>',
        '#include <dt-bindings/zmk/outputs.h>',
        '',
    ]
    if uses_mt and 'tapping_term_ms' in timing:
        out += [f"&mt {{ tapping-term-ms = <{timing['tapping_term_ms']}>; }};", '']
    out += ['/ {']
    if zmk.get('physical_layout'):
        out += ['    chosen {', f"        zmk,physical-layout = &{zmk['physical_layout']};", '    };', '']

    tri = base.get('firmware_features', {}).get('tri_layer')
    if tri:
        a, b, c = (ids.index(x) for x in tri)
        out += ['    conditional_layers {', '        compatible = "zmk,conditional-layers";',
                '        tri_layer {', f'            if-layers = <{a} {b}>;', f'            then-layer = <{c}>;',
                '        };', '    };', '']

    combos = [c for c in base.get('combos', []) if all(p in positions for p in c['keys'])]
    if combos:
        out += ['    combos {', '        compatible = "zmk,combos";']
        seen = set()
        for c in combos:
            node = 'combo_' + re.sub(r'\W+', '_', c['binding']).strip('_')
            while node in seen:
                node += '_'
            seen.add(node)
            idx = ' '.join(str(positions.index(p)) for p in c['keys'])
            out += [f'        {node} {{',
                    f"            timeout-ms = <{timing.get('combo_term_ms', 50)}>;",
                    f'            key-positions = <{idx}>;',
                    f"            bindings = <{to_zmk_text(c['binding'], ids)}>;",
                    '        };']
        out += ['    };', '']

    out += ['    keymap {', '        compatible = "zmk,keymap";']
    for layer in layers:
        cells = [to_zmk_text(b, ids) for b in layer['bindings']]
        width = max(len(c) for c in cells)
        out += ['', f"        layer_{layer['id']} {{", f'            display-name = "{layer["name"]}";',
                '            bindings = <']
        i = 0
        for n in row_lens:
            row = cells[i:i + n]
            i += n
            indent = ' ' * ((width + 2) * ((row_lens[0] - n) // 2)) if n < row_lens[0] else ''
            out.append(indent + '  '.join(c.ljust(width) for c in row).rstrip())
        out += ['            >;', '        };']
    blank = ' '.join(['&trans'] * len(positions))
    for n in range(zmk.get('reserved_layers', 0)):
        out += ['', f'        layer_reserved_{n} {{', f'            display-name = "SPARE{n + 1}";',
                '            status = "reserved";', f'            bindings = <{blank}>;', '        };']
    out += ['    };', '};', '']
    return '\n'.join(out)


# ---------------------------------------------------------------- import

def import_studio_dump(dump, profile):
    """Studio dump JSON (from studio_dump) -> list of base layers {id, name, keys}."""
    ids = [re.sub(r'[^a-z0-9]+', '_', l['name'].lower()).strip('_') for l in dump['layers']]
    layers = []
    for layer, lid in zip(dump['layers'], ids):
        bindings = [from_studio(raw, dump['behaviors'], ids) for raw in layer['raw']]
        if len(bindings) != len(profile['positions']):
            raise ValueError(f"layer {layer['name']}: {len(bindings)} bindings vs {len(profile['positions'])} positions")
        layers.append({'id': lid, 'name': layer['name'], 'keys': dict(zip(profile['positions'], bindings))})
    return layers
