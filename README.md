# zmk-config-Zen-2 — keyboard monorepo

ZMK firmware configs for every keyboard Jackson runs, in one place. CI
builds each on push and ships separate artifacts.

```
.
├── corneish-zen-v2/      Corneish Zen v2 (low-profile wireless, LOWPROKB)
├── corne-prospector/     Corne (Typeractive) with Prospector display dongle
├── corne-standalone/     Corne (Typeractive) plain — dongle-less
├── boards/               Custom boards + shields (board_root for all configs)
│   ├── lowprokb/corneish_zen_mod/
│   └── shields/corne_dongle/
├── prospector/case/      Prospector dongle case STLs (hardware reference)
├── vial/                 Vial layouts (bssk, crkbd_zen)
├── docs/                 Keymap visualizations + community notes
└── .github/workflows/    One job per keyboard
```

## Keyboards

| Config | Hardware | Topology | Notes |
| --- | --- | --- | --- |
| `corneish-zen-v2/` | Corneish Zen v2 halves (LOWPROKB) | Standard split | Custom boards under `boards/lowprokb/corneish_zen_mod/`. Left half has a `..._with_studio` variant for live editing via ZMK Studio. |
| `corne-prospector/` | Typeractive Corne (nice!nano v2) + XIAO BLE Prospector dongle | Dongle = central, both halves = peripherals | Dongle owns the keymap. Custom `corne_dongle` shield + `prospector_adapter` shield from [carrefinho/prospector-zmk-module](https://github.com/carrefinho/prospector-zmk-module) (`feat/new-status-screens`). ZMK Studio enabled (USB to dongle). |
| `corne-standalone/` | Typeractive Corne (nice!nano v2) + nice!view displays | Left = central, right = peripheral | Same W-CORNE keymap as the dongle build. Works fully on its own — no dongle. Left half has a `..._with_studio` variant. |

### Corne: with or without the dongle

The two Corne configs are **interchangeable on the same hardware** — pick by
which firmware set you flash:

- **`corne-prospector`** → keyboard needs the dongle to function (halves are
  peripherals to it). Prospector display shows live layer, batteries,
  modifiers. Sleeker desk presence, more pieces.
- **`corne-standalone`** → keyboard works on its own. nice!view displays on
  the halves show their own status. Dongle does nothing (the Prospector
  module is central-only — it has no peripheral or scanner mode on the
  branch we use).

Switching: flash all three devices with the matching set. Clear BLE bonds
first if pairing roles change (use the `settings_reset` shield — see
`corne-prospector/build.yaml` for ready-made targets, applies to both
configs since both run on nice!nano v2).

## Build

CI is on push to `main` (and PRs / manual dispatch). [Actions tab][actions]
→ each keyboard has its own job and artifact:

- `corneish-zen-v2.zip`
- `corne-prospector.zip`
- `corne-standalone.zip`

Each archive contains the `.uf2` files for that keyboard. Drag onto the
mounted bootloader volume (double-tap reset on the target device).

[actions]: https://github.com/toml0006/zmk-config-zen-2/actions

### Local build

Not set up by default. ZMK's standard local-build flow works if you point
`west init -l` at the desired config dir, e.g.:

```sh
west init -l corne-prospector/config
west update
west build -s zmk/app -d build -b "xiao_ble//zmk" -- \
    -DSHIELD="corne_dongle prospector_adapter" \
    -DZMK_CONFIG="$PWD/corne-prospector/config" \
    -DZMK_EXTRA_MODULES="$PWD"
```

(The `ZMK_EXTRA_MODULES=$PWD` is what makes the repo's `boards/` reachable
for custom shields like `corne_dongle`. CI does the same via the reusable
workflow.)

## Flashing

Each keyboard's directory has its own notes — see:

- [`corne-prospector/README.md`](corne-prospector/README.md) — dongle pairing
  order, settings_reset, Prospector display options
- The Corneish Zen instructions previously at the repo root (now archived in
  `docs/`) for the V1/V2 PCB distinction

General nice!nano v2 / XIAO BLE flashing: double-tap reset → device mounts
as `NICENANO` or `XIAO-SENSE` → drag the `.uf2` onto it.

## Resources

- [ZMK Firmware](https://github.com/zmkfirmware/zmk)
- [ZMK Docs](https://zmk.dev/docs) — especially the
  [Zephyr 4.1 / ZMK board variant](https://zmk.dev/blog/2025/12/09/zephyr-4-1)
  note (boards like `nice_nano` now need the `//zmk` variant qualifier and a
  revision, e.g. `nice_nano@2.0.0//zmk`)
- [Prospector hardware](https://github.com/carrefinho/prospector) /
  [Prospector ZMK module](https://github.com/carrefinho/prospector-zmk-module)
- [ZMK Discord](https://zmk.dev/community/discord/invite)
