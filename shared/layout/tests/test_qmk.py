import pytest

from kbsync.layout import load_base, load_profile
from kbsync.qmk import to_qmk, to_qmk_or_none
from kbsync.vial import matrix_map, plan

IDS = ['qwerty', 'number', 'symbol', 'function', 'spare2']


# Expected values are keycodes read back from the W-CORNE and corne_ec Vial boards.
@pytest.mark.parametrize('binding,kc', [
    ('tab', 0x002B), ('lcmd', 0x00E3), ('excl', 0x021E), ('shift+cmd+lbkt', 0x0A2F),
    ('cmd+grave', 0x0835), ('ctrl+shift+cmd+n4', 0x0B21), ('cmd+space', 0x082C),
    ('c_rw', 0x00BC), ('c_pp', 0x00AE), ('c_ff', 0x00BB), ('c_vol_dn', 0x00AA), ('c_mute', 0x00A8),
    ('c_vol_up', 0x00A9), ('c_bri_dn', 0x00BE), ('c_bri_up', 0x00BD), ('f13', 0x0068), ('f24', 0x0073),
    ('mo(number)', 0x5221), ('mo(symbol)', 0x5222), ('mo(function)', 0x5223),
    ('trans', 0x0001), ('none', 0x0000), ('qmk(0x7c00)', 0x7C00),
    ('mt(lctrl, z)', 0x211D), ('mt(rshift, fslh)', 0x3238), ('lt(number, space)', 0x412C),
])
def test_keycodes(binding, kc):
    assert to_qmk(binding, IDS) == kc


@pytest.mark.parametrize('binding', ['globe', 'bt_sel(0)', 'bt_clr', 'studio_unlock', 'consumer(0x71)'])
def test_degraded(binding):
    assert to_qmk_or_none(binding, IDS) == (0, to_qmk_or_none(binding, IDS)[1])
    assert to_qmk_or_none(binding, IDS)[1]


def test_corne_ec_matrix():
    mm = matrix_map(load_profile('corne-ec'))
    assert len(mm) == 46
    assert mm['L00'] == (0, 0) and mm['L05'] == (0, 5) and mm['LX0'] == (0, 6)
    assert mm['R00'] == (4, 6) and mm['R05'] == (4, 1) and mm['RX1'] == (5, 0)
    assert mm['L30'] == (3, 4) and mm['L32'] == (3, 6) and mm['R32'] == (7, 0) and mm['R30'] == (7, 2)


def test_corne_ec_plan():
    target, combos, degraded = plan(load_base(), load_profile('corne-ec'), 8)
    assert len(target) == 46 * 8
    # base layer lands where the board had the same keys before
    assert target[(0, 0, 0)] == 0x2B and target[(0, 4, 6)] == 0x2A   # Tab, Bspc
    assert target[(0, 3, 4)] == 0xE3 and target[(0, 3, 6)] == 0x2C   # Cmd, Space
    assert target[(0, 7, 0)] == 0x28 and target[(0, 5, 5)] == 0x33   # Enter, ;
    assert target[(0, 0, 6)] == 0x0A2F and target[(0, 4, 0)] == 0x0A30  # tab prev / next
    assert target[(1, 0, 6)] == 0x0A35 and target[(2, 4, 0)] == 0x0835  # window prev (Lower) / next (Raise)
    assert target[(3, 0, 6)] == 0x01 and target[(1, 1, 6)] == 0x01      # Function layer / other inner keys: trans
    assert target[(3, 0, 0)] == 0x7C00                                 # override: QK_BOOT
    assert target[(5, 0, 0)] == 0x01                                   # layers past base are transparent
    assert [0x0D, 0x0E, 0, 0, 0x29] in combos                          # J+K -> Esc
    assert {(p, b) for _, p, b, _ in degraded} >= {('LX1', 'globe'), ('R00', 'bt_clr')}
