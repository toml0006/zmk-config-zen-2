"""Safe evaluator for the C constant expressions used in ZMK dt-bindings headers
and keymap binding parameters (no Python eval)."""

import re

_TOKEN = re.compile(r'\s*(?:(0x[0-9a-fA-F]+|\d+)|([A-Za-z_]\w*)|(<<|>>|[()|&~,]))')

MOD_BITS = {'LC': 0x01, 'LS': 0x02, 'LA': 0x04, 'LG': 0x08, 'RC': 0x10, 'RS': 0x20, 'RA': 0x40, 'RG': 0x80}


def _tokens(text):
    pos, out = 0, []
    text = text.strip()
    while pos < len(text):
        m = _TOKEN.match(text, pos)
        if not m or m.end() == pos:
            raise ValueError(f'cannot tokenize {text!r} at {pos}')
        num, ident, op = m.groups()
        out.append(('num', int(num, 0)) if num else ('id', ident) if ident else ('op', op))
        pos = m.end()
    return out


def evaluate(text, resolve):
    """Evaluate `text`; `resolve(name)` returns the int value of an identifier."""
    toks = _tokens(text)
    i = 0

    def peek(v=None):
        return i < len(toks) and (v is None or toks[i] == ('op', v))

    def take(v):
        nonlocal i
        if not peek(v):
            raise ValueError(f'expected {v!r} in {text!r}')
        i += 1

    def atom():
        nonlocal i
        if peek('~'):
            i += 1
            return ~atom()
        if peek('('):
            i += 1
            v = or_()
            take(')')
            return v
        kind, val = toks[i]
        i += 1
        if kind == 'num':
            return val
        if kind != 'id':
            raise ValueError(f'unexpected {val!r} in {text!r}')
        if not peek('('):
            return resolve(val)
        i += 1
        args = [or_()]
        while peek(','):
            i += 1
            args.append(or_())
        take(')')
        if val in MOD_BITS and len(args) == 1:
            return (MOD_BITS[val] << 24) | args[0]
        if val == 'ZMK_HID_USAGE' and len(args) == 2:
            return (args[0] << 16) | args[1]
        if val == 'APPLY_MODS' and len(args) == 2:
            return (args[0] << 24) | args[1]
        raise ValueError(f'unknown macro {val}({len(args)} args) in {text!r}')

    def shift():
        nonlocal i
        v = atom()
        while peek('<<') or peek('>>'):
            op = toks[i][1]
            i += 1
            r = atom()
            v = v << r if op == '<<' else v >> r
        return v

    def and_():
        nonlocal i
        v = shift()
        while peek('&'):
            i += 1
            v &= shift()
        return v

    def or_():
        nonlocal i
        v = and_()
        while peek('|'):
            i += 1
            v |= and_()
        return v

    v = or_()
    if i != len(toks):
        raise ValueError(f'trailing tokens in {text!r}')
    return v
