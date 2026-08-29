# zmk-config-Zen-2 — keyboard monorepo

ZMK firmware configs for every keyboard Jackson runs, in one place. CI
builds each on push and ships separate artifacts.

Organized **one folder per physical keyboard** under `keyboards/`. Shared
hardware assets live in `shared/`. ZMK build infrastructure (`boards/`,
`zephyr/`, `.github/`) stays at the repo root — CI needs it there.

```
.
├── keyboards/                        One folder per board I own
│   ├── corneish-zen/                 Corneish Zen v2 (low-profile wireless, LOWPROKB)  [ZMK]
│   ├── typeractive/                  Typeractive Corne — 2 units, 3 flashable builds   [ZMK]
│   │   ├── prospector/               Dongle = central, both halves = peripherals
│   │   ├── standalone/               Left = central, right = peripheral (no dongle)
│   │   └── scanner/                  Standalone + passive Prospector observer
│   ├── dasbob/                       DASBOB split                                      [Vial/QMK]
│   ├── totem/                        Totem split — firmware/ + case/                   [ZMK]
│   ├── th40/                         40% Corne-matched layout        (planned)         [VIA/QMK]
│   ├── iris/                         Iris split                      (planned)
│   ├── nuphy-air-v3/                 Nuphy Air V3, off-the-shelf     (planned)         [QMK/VIA]
│   ├── corne-mx-2.4ghz/             Corne, MX, 2.4GHz wireless      (planned)
│   └── corne-ec-wired/             Corne, electro-capacitive, wired (planned)
│
├── boards/                           Custom ZMK boards + shields (board_root)
│   ├── lowprokb/corneish_zen_mod/
│   └── shields/corne_dongle/
├── zephyr/                           ZMK module marker (west)
│
├── shared/                           Not tied to one board
│   ├── keycaps/                      Parametric keycap generator (Fusion)
│   ├── switchbox/                    Parametric switch storage box
│   ├── prospector/case/             Prospector dongle case STLs
│   └── cases/                        Choc keycap pads, travel case
│
├── vial/                             Vial layouts (bssk, crkbd_zen)
├── docs/                             Keymap visualizations + community notes
└── .github/workflows/               One job per keyboard
```

## Keyboards

| Config | Hardware | Topology | Notes |
| --- | --- | --- | --- |
| `keyboards/corneish-zen/` | Corneish Zen v2 halves (LOWPROKB) | Standard split | Custom boards under `boards/lowprokb/corneish_zen_mod/`. Left half has a `..._with_studio` variant for live editing via ZMK Studio. |
| `keyboards/typeractive/prospector/` | Typeractive Corne (nice!nano v2) + XIAO BLE Prospector dongle | Dongle = central, both halves = peripherals | Dongle owns the keymap. Custom `corne_dongle` shield + `prospector_adapter` shield from [carrefinho/prospector-zmk-module](https://github.com/carrefinho/prospector-zmk-module) (`feat/new-status-screens`). ZMK Studio enabled (USB to dongle). |
| `keyboards/typeractive/standalone/` | Typeractive Corne (nice!nano v2) + nice!view displays | Left = central, right = peripheral | Same W-CORNE keymap as the dongle build. Works fully on its own — no dongle. Left half has a `..._with_studio` variant. |
| `keyboards/typeractive/scanner/` | Same as standalone + a Prospector unit acting as a passive scanner | Left = central, right = peripheral, scanner = observer (no link) | Keyboard fully independent; the Prospector listens to BLE status adverts and renders them. Uses the [t-ogura fork](https://github.com/t-ogura/zmk-config-prospector) of the prospector module (`v2.2.1`) — supplies the broadcaster (`CONFIG_ZMK_STATUS_ADVERTISEMENT`) and `prospector_scanner` shield. |

### Corne: three flavors

All three Corne configs run on **the same nice!nano v2 halves** — pick by
which firmware set you flash:

- **`corne-prospector`** → dongle = central, both halves = peripherals.
  Keyboard does not work without the dongle. Prospector display shows
  layer / batteries / modifiers fed from the central. Uses the
  [carrefinho fork](https://github.com/carrefinho/prospector-zmk-module)
  of the Prospector module (`feat/new-status-screens`).
- **`corne-standalone`** → left = central, right = peripheral. Keyboard
  works on its own; nice!view displays on the halves show their own
  status. No dongle in the picture.
- **`corne-scanner`** → same standalone topology, plus the Prospector
  acts as a **passive scanner** that listens to BLE status adverts the
  central broadcasts. Unplug or move the scanner; keyboard keeps
  working. Uses the [t-ogura fork](https://github.com/t-ogura/zmk-config-prospector)
  of the Prospector module (`v2.2.1`), which adds the broadcaster and a
  `prospector_scanner` shield.

The two Prospector configs cannot share a Prospector simultaneously —
flash whichever firmware matches the topology you want on the dongle.

Switching: flash all three devices with the matching set. Clear BLE bonds
first if pairing roles change (use the `settings_reset` shield — see
`keyboards/typeractive/prospector/build.yaml` for ready-made targets, applies to both
configs since both run on nice!nano v2).

## Build

CI is on push to `main` (and PRs / manual dispatch). [Actions tab][actions]
→ each keyboard has its own job and artifact:

- `corneish-zen-v2.zip`
- `corne-prospector.zip`
- `corne-standalone.zip`
- `corne-scanner.zip`

Each archive contains the `.uf2` files for that keyboard. Drag onto the
mounted bootloader volume (double-tap reset on the target device).

[actions]: https://github.com/toml0006/zmk-config-zen-2/actions

### Local build

Not set up by default. ZMK's standard local-build flow works if you point
`west init -l` at the desired config dir, e.g.:

```sh
west init -l keyboards/typeractive/prospector/config
west update
west build -s zmk/app -d build -b "xiao_ble//zmk" -- \
    -DSHIELD="corne_dongle prospector_adapter" \
    -DZMK_CONFIG="$PWD/keyboards/typeractive/prospector/config" \
    -DZMK_EXTRA_MODULES="$PWD"
```

(The `ZMK_EXTRA_MODULES=$PWD` is what makes the repo's `boards/` reachable
for custom shields like `corne_dongle`. CI does the same via the reusable
workflow.)

## Flashing

Each keyboard's directory has its own notes — see:

- [`keyboards/typeractive/prospector/README.md`](keyboards/typeractive/prospector/README.md) — dongle pairing
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
