# Layout sync — one layout, every board

**Date:** 2026-09-15
**Status:** approved design, step 1 in progress
**Seed layout:** `corne-base-fall-26` (Corneish Zen live keymap, 2026-09-15)

## Goal

One canonical layout drives every keyboard I use. Whichever board is my daily
driver, I can pull its live keymap, review the diff against the canonical
layout, merge it, and push the result to every other board — without
hand-porting.

## Fleet

| Board | Keys | Firmware | Live edit | Repo |
|---|---|---|---|---|
| Corneish Zen (daily) | 42 | ZMK + Studio | Studio RPC (USB) | `keyboards/corneish-zen` |
| Typeractive Corne ×2 | 42 | ZMK + Studio | Studio RPC | `keyboards/typeractive` |
| Corne v4 ×2 (incl. W-CORNE EC) | 46 | Vial | Vial raw HID | `keyboards/corne-ec-wired`, `vial/` |
| Totem | 38 | ZMK | Studio RPC (after reflash) | `keyboards/totem` |
| DASBOB | 36 | ZMK | Studio RPC (after reflash) | `keyboards/dasbob` |
| Epomaker TH40 | ~40, row-staggered | VIA/QMK | VIA raw HID | `keyboards/th40` |

(The 42-key count above totals three ZMK Cornes including the Zen.)

## Architecture

```
            pull (live read)                      push (live write + read-back)
 any board ────────────────► base.yaml ─────────────────────────► every board
                              ▲    │ generate
                  boards/*.yaml    └──► .keymap / .vil / VIA json (committed)
```

Everything lives in `shared/layout/`:

```
shared/layout/
  base.yaml            canonical layout (layers, combos, timing)
  boards/<board>.yaml  per-board profile: position map, overrides, local keys
  kbsync/              Python package + `kbsync` CLI
  tests/
```

### Canonical positions

Positions are named, not indexed, so boards with different key counts share
one vocabulary. `{L|R}{row}{col}`:

- `row`: 0 top, 1 home, 2 bottom, 3 thumb
- `col`: 0 = outermost (pinky column) … 5 = innermost (index stretch).
  Thumbs: 0 = outermost … 2 = innermost.

The 42-key Corne is `L00–L25`, `L30–L32`, `R00–R25`, `R30–R32`.

| Board | Positions present |
|---|---|
| 42-key Corne | all 42 |
| 46-key Corne v4 | all 42 + board-local `LX0 LX1 RX0 RX1` (inner column, top/bottom) |
| Totem (38) | cols 1–5 rows 0–2, `L20` + `R20` (outer pinky extras), thumbs |
| DASBOB (36) | cols 1–5 rows 0–2, thumbs |
| TH40 | best-effort map, defined in its profile (later) |

### Canonical key vocabulary

Firmware-neutral strings, parsed by `kbsync.keys`:

| Kind | Syntax | Examples |
|---|---|---|
| Plain key | name | `a`, `n1`, `tab`, `bspc`, `lctrl`, `lbkt`, `pg_up` |
| Modified key | `mods+key` | `cmd+shift+lbkt`, `ctrl+cmd+shift+n4` |
| Consumer | name or `consumer(0xNN)` | `c_pp`, `c_vol_up`, `globe`, `consumer(0x71)` |
| Layer | `mo(layer)`, `tog(layer)` | `mo(number)` |
| Mod-tap | `mt(mod, key)` | `mt(lctrl, z)` |
| Wireless/tooling | `bt_sel(n)`, `bt_clr`, `studio_unlock` | |
| Pass/none | `trans`, `none` | |

Layers are referenced by name. Each adapter declares which kinds it
supports and a **degrade rule** for the rest (`bt_*`/`studio_unlock` →
`none` on wired QMK; `globe` → custom keycode on QMK, see below).

### base.yaml

```yaml
name: corne-base-fall-26
layers:
  - id: base
    name: qwerty
    keys: { L00: tab, L01: q, ... }
combos:
  - { keys: [R14, R13], binding: esc }    # J+K
  - { keys: [L01, L02], binding: tab }    # Q+W
  - { keys: [R02, R01], binding: bspc }   # O+P
  - { keys: [R12, R11], binding: sqt }    # L+;
timing: { tapping_term_ms: 200, combo_term_ms: 40 }
firmware_features: { tri_layer: [number, symbol, function] }
```

### Board profile

```yaml
board: dasbob
firmware: zmk
positions: [L01, L02, ..., R32]          # physical order as the firmware sees it
overrides:                               # board-owned; never merged into base on pull
  base: { L21: mt(lctrl, z), R21: mt(lctrl, fslh), L22: mt(lshift, x), R22: mt(lshift, dot) }
local: {}                                # keys with no canonical position (e.g. LX0)
```

## Decisions

1. **Missing outer columns (Totem/DASBOB).**
   - Combos on **every** board: `J+K`=Esc, `Q+W`=Tab, `O+P`=BSPC, `L+;`=`'`.
   - Small boards only (profile overrides): hold `Z`/`/` = Ctrl, hold `X`/`.` = Shift.
   - Thumbs identical everywhere. Totem keeps Shift/Esc on its outer pinky extras (`L20`/`R20`).
   - I am a heavy Ctrl/Esc user; keep both one-motion.
2. **Push mode: hybrid.**
   - Generated files (keymap, combos, timing) are always committed.
   - Bindings are pushed live where the firmware allows, then read back and diffed.
   - Reflash only when combos, timing or layer count change — ZMK combos and timing are devicetree-only.
3. **46-key Vial inner keys (board-local).** `LX0` ⌘⇧[, `RX0` ⌘⇧], `LX1` Globe, `RX1` ⌃⌘⇧4.
4. **DASBOB runs ZMK.** `keyboards/dasbob/README.md` saying Vial is stale.

## Workflows

```
kbsync pull <board>        read live keymap → normalize → diff vs base → (approve) → write base.yaml
kbsync diff <board>        live board vs what base+profile would generate
kbsync gen [<board>|--all] write firmware files from base + profile
kbsync push <board>|--all  live-write bindings, then read back and verify
```

### Pull merge rules

- Only positions the source board has are merged. A 36-key pull never touches outer columns.
- Positions listed in the board's `overrides`/`local` are skipped.
- The diff is shown and must be approved before `base.yaml` changes; commit afterwards.

## Adapters

| Adapter | Read | Write | Files |
|---|---|---|---|
| `zmk` | Studio RPC over USB CDC (SOF 0xAB / ESC 0xAC / EOF 0xAD framed protobuf; `get_keymap` needs unlock) | `set_layer_binding` + `save_changes` | `<shield>.keymap` |
| `vial` | Vial raw HID (dynamic keymap get, combos, QMK settings) | same protocol | `.vil` + QMK keymap source |
| `via` | VIA raw HID dynamic keymap | same | VIA JSON |

Keycode tables come from source headers rather than hand-kept lists (ZMK
`dt-bindings/zmk/keys.h`; QMK `keycodes.h` for Vial/VIA).

## Firmware prerequisites (one-time)

- **ZMK boards without Studio** (Totem, DASBOB, second Typeractive builds as needed): Studio-enabled builds plus combos/timing → one reflash each.
- **Vial Cornes:** firmware needs `COMBO_ENABLE = yes`, a 46-key layout (current `vial/crkbd_zen` is `LAYOUT_split_3x6_3`, 42 keys, combos off), and a custom `GLOBE` keycode sending consumer usage 0x29D → one rebuild + reflash. Identify the actual W-CORNE QMK source first (USB `55d4:0461`, manufacturer "Pilot").
- **TH40:** check whether its VIA firmware can do combos and a custom Globe; if not, it gets the base layout without combos (its dedicated Esc/Tab/BSPC/`'` keys cover them).

## Verification

- **Round-trip:** device dump → `base.yaml` → generated `.keymap` must reproduce every device binding value exactly. This is the same 5×42 check already passed on the Zen.
- **Push:** every push ends with a pull and an empty diff.
- **Unit tests:** key vocabulary parse/format; ZMK usage encode/decode against `keys.h`; position maps (count and uniqueness per profile); combo position validity per board.

## Build order

1. Canonical schema, key vocabulary, ZMK codec; import the Zen dump → `base.yaml`; generate the Zen `.keymap`; round-trip test.
2. ZMK Studio pull/push/diff CLI on the Zen (reuse the Studio RPC client), plus the two Typeractive Cornes.
3. Vial adapter against the W-CORNE; Vial firmware with combos + Globe.
4. Totem and DASBOB profiles, combos/mod-tap overrides, reflash with Studio.
5. TH40 profile and VIA adapter.

## Out of scope

- Nuphy Air V3 and Iris (planned boards, not in the fleet above).
- Macros, tap-dance, encoders, RGB.
