import json

import pytest

from kbsync import zmk
from kbsync.layout import CANONICAL, REPO, dump_base, load_base, load_profile

DUMP = REPO / 'keyboards/corneish-zen/zen_keymap.json'


@pytest.fixture(scope='module')
def dump():
    return json.loads(DUMP.read_text())


@pytest.fixture(scope='module')
def zen():
    return load_profile('corneish-zen')


def test_corne42_positions():
    assert len(CANONICAL) == 42 == len(set(CANONICAL))
    assert CANONICAL[:12] == ['L00', 'L01', 'L02', 'L03', 'L04', 'L05', 'R05', 'R04', 'R03', 'R02', 'R01', 'R00']
    assert CANONICAL[36:] == ['L30', 'L31', 'L32', 'R32', 'R31', 'R30']


def test_zmk_text_round_trip():
    ids = ['base', 'number']
    for b in ['a', 'shift+cmd+lbkt', 'consumer(0x71)', 'mo(number)', 'mt(lctrl, z)', 'bt_sel(5)',
              'bt_clr', 'trans', 'studio_unlock', 'lt(number, space)', 'globe']:
        text = zmk.to_zmk_text(b, ids)
        assert zmk.from_triplet(*zmk.parse_zmk_binding(text), ids) == b, text


def test_base_yaml_round_trip(tmp_path):
    base = load_base()
    path = tmp_path / 'base.yaml'
    path.write_text(dump_base(base))
    again = load_base(path)
    assert again['layers'] == base['layers']
    assert again['combos'] == base['combos']


def test_combos_hit_intended_keys():
    base = load_base()
    home = base['layers'][0]['keys']
    wanted = {'esc': {'j', 'k'}, 'tab': {'q', 'w'}, 'bspc': {'o', 'p'}, 'sqt': {'l', 'semi'}}
    got = {c['binding']: {home[p] for p in c['keys']} for c in base['combos']}
    assert got == wanted


def test_import_matches_device(dump, zen):
    layers = zmk.import_studio_dump(dump, zen)
    ids = [l['id'] for l in layers]
    for layer, d in zip(layers, dump['layers']):
        for pos, raw in zip(zen['positions'], d['raw']):
            kind = zmk.STUDIO_KINDS[dump['behaviors'][str(raw[0])]]
            assert zmk.to_triplet(layer['keys'][pos], ids) == (kind, raw[1], raw[2])


def test_generated_keymap_reproduces_device(dump, zen):
    """The acceptance check from the spec: device dump == generated .keymap, binding for binding."""
    generated = [l for l in zmk.parse_keymap(zmk.generate_keymap(load_base(), zen)) if not l['reserved']]
    assert len(generated) == len(dump['layers'])
    for g, d in zip(generated, dump['layers']):
        want = [(zmk.STUDIO_KINDS[dump['behaviors'][str(r[0])]], r[1], r[2]) for r in d['raw']]
        assert g['bindings'] == want, d['name']


def test_generated_keymap_combo_positions(zen):
    text = zmk.generate_keymap(load_base(), zen)
    assert 'key-positions = <19 20>;' in text   # J+K
    assert 'bindings = <&kp ESC>;' in text
