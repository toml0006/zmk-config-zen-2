"""Canonical layout (base.yaml) and board profiles (boards/<board>.yaml)."""

import re
from pathlib import Path

import yaml

from .keys import normalize


def _corne42():
    rows = []
    for r in range(3):
        rows += [f'L{r}{c}' for c in range(6)] + [f'R{r}{c}' for c in reversed(range(6))]
    return rows + ['L30', 'L31', 'L32', 'R32', 'R31', 'R30']


# Position lists in firmware/physical order (left-to-right, top-to-bottom), plus row lengths for display.
GRIDS = {'corne42': (_corne42(), [12, 12, 12, 6])}
CANONICAL = GRIDS['corne42'][0]

ROOT = Path(__file__).resolve().parents[1]  # shared/layout
REPO = ROOT.parents[1]


def slug(name):
    return re.sub(r'[^a-z0-9]+', '_', name.lower()).strip('_')


# ---------------------------------------------------------------- base.yaml

def load_base(path=ROOT / 'base.yaml'):
    data = yaml.safe_load(Path(path).read_text())
    positions, _ = GRIDS[data.get('grid', 'corne42')]
    for layer in data['layers']:
        cells = [c for row in layer.pop('rows') for c in row]
        if len(cells) != len(positions):
            raise ValueError(f"layer {layer['id']}: {len(cells)} keys, grid needs {len(positions)}")
        layer['keys'] = {p: normalize(str(c)) for p, c in zip(positions, cells)}
    ids = [l['id'] for l in data['layers']]
    for combo in data.get('combos', []):
        for p in combo['keys']:
            if p not in positions:
                raise ValueError(f'combo {combo} uses unknown position {p}')
        combo['binding'] = normalize(combo['binding'])
    for layer_id in data.get('firmware_features', {}).get('tri_layer', []):
        if layer_id not in ids:
            raise ValueError(f'tri_layer references unknown layer {layer_id}')
    return data


_PLAIN = re.compile(r'^[a-z0-9_+()]+$')


def _scalar(s):
    return s if _PLAIN.match(s) else '"' + s.replace('"', '\\"') + '"'


def dump_base(base):
    """YAML text with each layer as an aligned grid in physical order."""
    grid = base.get('grid', 'corne42')
    positions, row_lens = GRIDS[grid]
    head = {k: v for k, v in base.items() if k not in ('layers', 'combos', 'timing', 'firmware_features')}
    out = [yaml.safe_dump(head, sort_keys=False).rstrip(), '', 'layers:']
    width = max(len(_scalar(k)) for layer in base['layers'] for k in layer['keys'].values())
    for layer in base['layers']:
        cells = [_scalar(layer['keys'][p]) for p in positions]
        rows, i = [], 0
        for n in row_lens:
            rows.append(cells[i:i + n])
            i += n
        name = yaml.safe_dump(layer['name'], default_style=None).removesuffix('\n...\n').strip()
        out += [f"  - id: {layer['id']}", f"    name: {name}", '    rows:']
        for row in rows:
            half = len(row) // 2
            left = ', '.join(c.ljust(width) for c in row[:half])
            right = ', '.join(c.ljust(width) for c in row[half:])
            pad = ' ' * ((width + 2) * (6 - half))  # keep thumb rows centred under the split
            out.append(f'      - [{pad}{left},   {right}]'.replace(' ]', ']'))
    for key in ('combos', 'timing', 'firmware_features'):
        if base.get(key):
            out += ['', yaml.safe_dump({key: base[key]}, sort_keys=False, default_flow_style=None).rstrip()]
    return '\n'.join(out) + '\n'


def save_base(base, path=ROOT / 'base.yaml'):
    Path(path).write_text(dump_base(base))


# ---------------------------------------------------------------- board profiles

def load_profile(board, root=ROOT):
    data = yaml.safe_load((root / 'boards' / f'{board}.yaml').read_text())
    if isinstance(data['positions'], str):
        data['positions'], data['row_lengths'] = GRIDS[data['positions']]
    positions = data['positions']
    if len(set(positions)) != len(positions):
        raise ValueError(f'{board}: duplicate positions')
    data.setdefault('overrides', {})
    data.setdefault('local', {})
    return data


def board_layers(base, profile):
    """Resolve base + overrides into per-layer binding lists in the board's position order."""
    layers = []
    for layer in base['layers']:
        over = profile['overrides'].get(layer['id'], {})
        layers.append({
            'id': layer['id'], 'name': layer['name'],
            'bindings': [normalize(over[p]) if p in over else layer['keys'].get(p, 'none')
                         for p in profile['positions']],
        })
    return layers
