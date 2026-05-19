# Corne + Prospector ZMK config

ZMK config for a **Typeractive Corne** (Choc, nice!nano v2) running with a
[Prospector](https://github.com/carrefinho/prospector) dongle as the split
central. Lives in the [keyboard monorepo](../README.md); the standalone
(no-dongle) counterpart is at [`../corne-standalone/`](../corne-standalone/).

## Topology

| Device                     | Board                  | Shield                            | Split role |
| -------------------------- | ---------------------- | --------------------------------- | ---------- |
| Corne left half            | `nice_nano@2.0.0//zmk` | `corne_left`                      | peripheral |
| Corne right half           | `nice_nano@2.0.0//zmk` | `corne_right`                     | peripheral |
| Prospector dongle (XIAO)   | `xiao_ble//zmk`        | `corne_dongle prospector_adapter` | central    |

The dongle owns the keymap; both halves are stock-shield split peripherals.
The custom `corne_dongle` shield lives at
[`../boards/shields/corne_dongle/`](../boards/shields/corne_dongle/) (root
`boards/` is the shared board_root for the monorepo). It has no keys —
the dongle is keyless and uses a mock kscan.

## Layout

```
corne-prospector/
  build.yaml                       5 build targets (3 firmware + 2 settings_reset)
  config/
    west.yml                       ZMK main + prospector-zmk-module (feat/new-status-screens)
    corne_left.conf                left  half — split peripheral
    corne_right.conf               right half — split peripheral
    corne_dongle.conf              dongle — split central + ZMK Studio + display options
    corne.keymap                   the keymap (4 layers; W-CORNE port)
    corne_dongle.keymap            #includes corne.keymap
```

## Building

Push to `main` — the [monorepo workflow](../.github/workflows/build.yml)
builds this config and uploads `corne-prospector.zip` as an Actions
artifact. The archive contains:

- `corne_left.uf2` / `corne_right.uf2` — split peripherals
- `corne_prospector_dongle.uf2` — split central + ZMK Studio
- `settings_reset_nice_nano.uf2` / `settings_reset_xiao.uf2` — wipe BLE
  bonds (flash, double-tap reset again, then flash the real firmware)

Targets ZMK `main` (Zephyr 4.1). Board IDs use the new variant syntax
(`nice_nano@2.0.0//zmk`, `xiao_ble//zmk`) per
[the Dec 2025 ZMK blog](https://zmk.dev/blog/2025/12/09/zephyr-4-1#zmk-board-variant).
The Prospector module pin is the `feat/new-status-screens` branch per its
[module README](https://github.com/carrefinho/prospector-zmk-module).

## Flashing & pairing

1. Flash `corne_left`, `corne_right`, and `corne_prospector_dongle` to their
   respective devices (double-tap reset → drag `.uf2` onto the USB mount).
2. **Pair the LEFT half first, then the RIGHT half.** Peripheral connection
   order sets matrix slots: left → columns 0-5, right → columns 6-11. Wrong
   order = mirrored/scrambled right half and a swapped battery widget.
3. If pairing fails after a role change (e.g. flipping between this and the
   standalone Corne config), flash `settings_reset_*.uf2` first to wipe
   stale BLE bonds, then flash the real firmware.

## ZMK Studio

Enabled on the dongle build (`CONFIG_ZMK_STUDIO=y` + the
`studio-rpc-usb-uart` snippet). Plug the dongle into a host via USB-C and
open [ZMK Studio](https://zmk.studio); press the FN-layer top-right key
(`&studio_unlock`) to unlock the keyboard for live edits.

## Customising the display

Edit `config/corne_dongle.conf`. Options
([module Kconfig](https://github.com/carrefinho/prospector-zmk-module/blob/feat/new-status-screens/Kconfig)):

- `CONFIG_PROSPECTOR_USE_AMBIENT_LIGHT_SENSOR` — `n` if the build has no
  APDS9960 sensor (the `no_sensor` case).
- `CONFIG_PROSPECTOR_FIXED_BRIGHTNESS` — 1-100, used when the sensor is off.
- `CONFIG_PROSPECTOR_ROTATE_DISPLAY_180` — flip the screen.
- Status-screen layout (`PROSPECTOR_STATUS_SCREEN_{CLASSIC,RADII,FIELD,OPERATOR}`)
  — pick one.

The `prospector_adapter.overlay` exposes color themes
(`prospector_{green,blue,red,purple}_theme`) — reference them from the
overlay if you want to switch palette.
