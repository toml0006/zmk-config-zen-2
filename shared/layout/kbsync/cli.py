"""kbsync — keep one canonical layout in sync across keyboards."""

import argparse
import json
import sys
from pathlib import Path

from . import vial, zmk, zmk_table
from .layout import REPO, ROOT, dump_base, load_base, load_profile, save_base


def cmd_import_dump(args):
    profile = load_profile(args.board)
    dump = json.loads(Path(args.dump).read_text())
    layers = zmk.import_studio_dump(dump, profile)
    base_path = ROOT / 'base.yaml'
    base = load_base(base_path) if base_path.exists() else {'name': args.name, 'grid': 'corne42'}
    base['layers'] = layers
    save_base(base, base_path)
    load_base(base_path)  # validate what we wrote
    print(f'wrote {base_path.relative_to(REPO)}: {len(layers)} layers from {args.board}')


def cmd_gen(args):
    base = load_base()
    rc = 0
    for board in args.boards:
        profile = load_profile(board)
        if profile['firmware'] != 'zmk':
            sys.exit(f"{board}: firmware {profile['firmware']} not supported yet")
        text = zmk.generate_keymap(base, profile)
        path = REPO / profile['keymap']
        if args.check:
            same = path.exists() and path.read_text() == text
            print(f"{board}: {'up to date' if same else 'OUT OF DATE'}")
            rc |= not same
        else:
            path.write_text(text)
            print(f'{board}: wrote {profile["keymap"]}')
    sys.exit(rc)


def cmd_verify_dump(args):
    """Generated .keymap for <board> must reproduce every binding in a Studio dump."""
    profile = load_profile(args.board)
    dump = json.loads(Path(args.dump).read_text())
    generated = zmk.parse_keymap(zmk.generate_keymap(load_base(), profile))
    live = [l for l in generated if not l['reserved']]
    bad = 0
    if len(live) != len(dump['layers']):
        print(f"layer count: generated {len(live)} vs device {len(dump['layers'])}")
        bad += 1
    for g, d in zip(live, dump['layers']):
        for i, (got, raw) in enumerate(zip(g['bindings'], d['raw'])):
            want = (zmk.STUDIO_KINDS[dump['behaviors'][str(raw[0])]], raw[1], raw[2])
            if got != want:
                bad += 1
                print(f"MISMATCH {d['name']}[{profile['positions'][i]}]: generated {got} device {want}")
    total = sum(len(d['raw']) for d in dump['layers'])
    print(f'{args.board}: {total - bad}/{total} bindings match the device dump')
    sys.exit(1 if bad else 0)


def cmd_push(args):
    profile = load_profile(args.board)
    if profile['firmware'] != 'vial':
        sys.exit(f"{args.board}: live push supports vial boards so far (firmware: {profile['firmware']})")
    ok = vial.push(load_base(), profile, dry_run=args.dry_run)
    sys.exit(0 if ok else 1)


def cmd_restore(args):
    ok = vial.restore(load_profile(args.board), Path(args.backup).resolve())
    sys.exit(0 if ok else 1)


def cmd_zmk_table(args):
    out = ROOT / 'kbsync' / 'data' / 'zmk_keys.json'
    zmk_table.write(args.include_dir, out)
    print(f'wrote {out.relative_to(REPO)}')


def main(argv=None):
    p = argparse.ArgumentParser(prog='kbsync', description=__doc__)
    sub = p.add_subparsers(required=True)

    s = sub.add_parser('import-dump', help='replace base.yaml layers with a ZMK Studio dump')
    s.add_argument('board')
    s.add_argument('dump')
    s.add_argument('--name', default='corne-base')
    s.set_defaults(fn=cmd_import_dump)

    s = sub.add_parser('gen', help='generate firmware keymap files from base.yaml')
    s.add_argument('boards', nargs='+')
    s.add_argument('--check', action='store_true', help='exit 1 if files are out of date')
    s.set_defaults(fn=cmd_gen)

    s = sub.add_parser('verify-dump', help='check a generated keymap reproduces a Studio dump')
    s.add_argument('board')
    s.add_argument('dump')
    s.set_defaults(fn=cmd_verify_dump)

    s = sub.add_parser('push', help='write base.yaml to a connected board live (backs up first, then verifies)')
    s.add_argument('board')
    s.add_argument('--dry-run', action='store_true', help='show what would change without writing')
    s.set_defaults(fn=cmd_push)

    s = sub.add_parser('restore', help='write a backup taken by push back to the board')
    s.add_argument('board')
    s.add_argument('backup')
    s.set_defaults(fn=cmd_restore)

    s = sub.add_parser('zmk-table', help='rebuild kbsync/data/zmk_keys.json from ZMK headers')
    s.add_argument('include_dir', help='zmk/app/include/dt-bindings/zmk')
    s.set_defaults(fn=cmd_zmk_table)

    args = p.parse_args(argv)
    args.fn(args)


if __name__ == '__main__':
    main()
