"""Vial adapter: plan a board's keymap from base + profile, back up, push live, verify."""

import json
import time

from .keys import normalize
from .layout import REPO, board_layers
from .qmk import to_qmk_or_none
from .vialhid import Vial


def matrix_map(profile):
    """Canonical/local position -> (row, col)."""
    m, out = profile['matrix'], {}
    for side, spec in (('L', m['left']), ('R', m['right'])):
        for r, row in enumerate(spec['rows']):
            for c, col in enumerate(spec['cols']):
                out[f'{side}{r}{c}'] = (row, col)
        for c, rc in enumerate(spec['thumbs']):
            out[f'{side}3{c}'] = tuple(rc)
    out.update({pos: tuple(rc) for pos, rc in m.get('extra', {}).items()})
    if len(set(out.values())) != len(out):
        raise ValueError(f"{profile['board']}: two positions share a matrix cell")
    return out


def plan(base, profile, layer_count):
    """Target keycodes {(layer, row, col): kc}, combos [[k1..k4, out]], degraded [(layer, pos, binding, why)]."""
    ids = [l['id'] for l in base['layers']]
    if len(ids) > layer_count:
        raise ValueError(f"{profile['board']} has {layer_count} layers, base needs {len(ids)}")
    layers = board_layers(base, profile)
    positions = profile['positions']
    # firmware-specific keycodes for canonical keys, e.g. {globe: 0x7e03} once the firmware has it
    custom = {normalize(k): f'qmk(0x{v:04x})' for k, v in (profile.get('qmk_keycodes') or {}).items()}
    target, degraded = {}, []
    for li in range(layer_count):
        for pos, rc in matrix_map(profile).items():
            if li >= len(layers):
                binding = 'trans'
            elif pos in positions:
                binding = layers[li]['bindings'][positions.index(pos)]
            elif pos in profile['local']:
                spec = profile['local'][pos]
                per_layer = spec if isinstance(spec, dict) else {ids[0]: spec}  # plain value = first layer only
                binding = normalize(per_layer[ids[li]]) if ids[li] in per_layer else 'trans'
            else:
                binding = 'trans'
            kc, why = to_qmk_or_none(custom.get(binding, binding), ids)
            if why:
                degraded.append((ids[li] if li < len(ids) else li, pos, binding, why))
            target[(li, *rc)] = kc

    combos = []
    first = layers[0]['bindings']
    for combo in base.get('combos', []):
        if not all(p in positions for p in combo['keys']):
            continue
        keys = [to_qmk_or_none(custom.get(b, b), ids)[0] for b in (first[positions.index(p)] for p in combo['keys'])]
        out, why = to_qmk_or_none(custom.get(combo['binding'], combo['binding']), ids)
        if why:
            degraded.append(('combo', '+'.join(combo['keys']), combo['binding'], why))
        combos.append((keys + [0, 0, 0, 0])[:4] + [out])
    return target, combos, degraded


def _open(profile):
    v = Vial(profile['usb']['vid'], profile['usb']['pid'])
    if (proto := v.vial_protocol()) < 6:
        v.close()
        raise IOError(f'Vial protocol {proto} uses pre-0.19 QMK keycodes; not supported')
    d = v.definition()
    return v, d['matrix']['rows'], d['matrix']['cols']


def backup(v, profile, rows, cols):
    data = {'board': profile['board'], 'product': v.product, 'taken': time.strftime('%Y-%m-%dT%H:%M:%S%z'),
            'matrix': [rows, cols], 'keymap': v.keymap(rows, cols),
            'combos': [v.combo_get(i) for i in range(v.combo_count())]}
    path = REPO / profile['backup_dir'] / f"{profile['board']}-{time.strftime('%Y%m%d-%H%M%S')}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data) + '\n')
    return data, path


def push(base, profile, dry_run=False, log=print):
    v, rows, cols = _open(profile)
    try:
        current = v.keymap(rows, cols)
        target, combos, degraded = plan(base, profile, len(current))
        ncombo = v.combo_count()
        if len(combos) > ncombo:
            raise ValueError(f'{len(combos)} combos, board has {ncombo} slots')
        cur_combos = [v.combo_get(i) for i in range(ncombo)]
        changes = {k: kc for k, kc in target.items() if current[k[0]][k[1]][k[2]] != kc}
        combo_changes = {i: e for i, e in enumerate(combos) if cur_combos[i] != e}
        stray = [i for i in range(len(combos), ncombo) if any(cur_combos[i])]

        log(f"{profile['board']} ({v.product}): {len(current)} layers, {rows}x{cols} matrix, unlocked={v.unlocked()}")
        per_layer = {}
        for (l, _, _) in changes:
            per_layer[l] = per_layer.get(l, 0) + 1
        log(f'key changes: {len(changes)} {dict(sorted(per_layer.items()))}; combo changes: {len(combo_changes)}')
        for layer, pos, binding, why in degraded:
            log(f'  degraded -> KC_NO  {layer}[{pos}] {binding}: {why}')
        if stray:
            log(f'  note: combo slots {stray} are in use and left untouched')
        if dry_run:
            return True

        _, path = backup(v, profile, rows, cols)
        log(f'backup: {path.relative_to(REPO)}')
        for (l, r, c), kc in changes.items():
            v.set_key(l, r, c, kc)
        for i, e in combo_changes.items():
            v.combo_set(i, e)

        after = v.keymap(rows, cols)
        bad = [k for k, kc in target.items() if after[k[0]][k[1]][k[2]] != kc]
        bad_combos = [i for i, e in enumerate(combos) if v.combo_get(i) != e]
        for k in bad:
            log(f'  VERIFY FAIL key {k}: wanted {target[k]:04x} got {after[k[0]][k[1]][k[2]]:04x}')
        for i in bad_combos:
            log(f'  VERIFY FAIL combo {i}')
        log(f'verified: {len(target) - len(bad)}/{len(target)} keys, {len(combos) - len(bad_combos)}/{len(combos)} combos')
        return not bad and not bad_combos
    finally:
        v.close()


def restore(profile, backup_path, log=print):
    data = json.loads(backup_path.read_text())
    v, rows, cols = _open(profile)
    try:
        if [rows, cols] != data['matrix']:
            raise ValueError('backup matrix does not match the board')
        current = v.keymap(rows, cols)
        n = 0
        for l, layer in enumerate(data['keymap'][:len(current)]):
            for r, row in enumerate(layer):
                for c, kc in enumerate(row):
                    if current[l][r][c] != kc:
                        v.set_key(l, r, c, kc)
                        n += 1
        for i, e in enumerate(data['combos'][:v.combo_count()]):
            if v.combo_get(i) != e:
                v.combo_set(i, e)
        ok = v.keymap(rows, cols)[:len(data['keymap'])] == data['keymap'][:len(current)]
        log(f'restored {n} keys from {backup_path.name}; keymap matches backup: {ok}')
        return ok
    finally:
        v.close()
