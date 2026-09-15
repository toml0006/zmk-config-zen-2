import pytest

from kbsync.expr import evaluate
from kbsync.keys import name_to_usage, normalize, parse_binding, table, usage_to_name


def test_every_named_usage_round_trips():
    _, _, preferred = table()
    for v in preferred:
        assert name_to_usage(usage_to_name(v)) == v


@pytest.mark.parametrize('value,name', [
    (0x700e0, 'lctrl'),
    (0x7002f, 'lbkt'),
    (0xa07002f, 'shift+cmd+lbkt'),
    (0xb070021, 'ctrl+shift+cmd+n4'),
    (0x207001e, 'excl'),          # implicit-shift names win over shift+n1
    (0xc029d, 'globe'),
    (0xc0071, 'consumer(0x71)'),  # no ZMK name
    (0x70029, 'esc'),
])
def test_names(value, name):
    assert usage_to_name(value) == name
    assert name_to_usage(name) == value


def test_aliases_normalize():
    assert normalize('shift+n1') == 'excl'
    assert normalize('LCTL') == 'lctrl'
    assert normalize('mt(LCTRL,Z)') == 'mt(lctrl, z)'


def test_parse_binding():
    assert parse_binding('mo(number)') == ('mo', ('number',))
    assert parse_binding('consumer(0x71)') == ('kp', ('consumer(0x71)',))
    assert parse_binding('bt_clr') == ('bt_clr', ())
    with pytest.raises(ValueError):
        parse_binding('not_a_key')
    with pytest.raises(ValueError):
        parse_binding('hyper+a')


def test_expr():
    values, _, _ = table()
    assert evaluate('LC(LS(LG(N4)))', values.__getitem__) == 0xb070021
    assert evaluate('(ZMK_HID_USAGE(HID_USAGE_CONSUMER, 0x71))', values.__getitem__) == 0xc0071
