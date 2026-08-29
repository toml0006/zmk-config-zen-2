# Corne (standalone) ZMK config

ZMK config for a **Typeractive Corne** (Choc, nice!nano v2) with nice!view
displays and **no dongle** — left half is the split central, right half is
the peripheral. Lives in the [keyboard monorepo](../README.md); the
dongle counterpart is at
[`../corne-prospector/`](../corne-prospector/).

## Topology

| Device           | Board                  | Shield                                | Split role |
| ---------------- | ---------------------- | ------------------------------------- | ---------- |
| Corne left half  | `nice_nano@2.0.0//zmk` | `corne_left nice_view_adapter nice_view`  | central    |
| Corne right half | `nice_nano@2.0.0//zmk` | `corne_right nice_view_adapter nice_view` | peripheral |

The left half owns the keymap and connects to the host. nice!view displays
on both halves show layer / battery / status. No custom boards or shields
— everything is stock ZMK.

## Layout

```
corne-standalone/
  build.yaml                       3 build targets
  config/
    west.yml                       ZMK main
    corne.conf                     display + sleep config
    corne.keymap                   W-CORNE keymap (4 layers)
```

## Building

Push to `main` — the [monorepo workflow](../.github/workflows/build.yml)
builds this config and uploads `corne-standalone.zip` as an Actions
artifact. The archive contains:

- `corne_left.uf2` / `corne_right.uf2` — split central + peripheral
- `corne_left_with_studio.uf2` — left-half variant with ZMK Studio enabled
  (`-DCONFIG_ZMK_STUDIO=y` + `studio-rpc-usb-uart` snippet). Flash this
  *instead of* the plain `corne_left.uf2` to use Studio over USB on the
  left half.

## Flashing

Double-tap reset on each half → mounts as `NICENANO` → drag the matching
`.uf2`. If swapping between this and the dongle config, BLE roles change —
flash `settings_reset_nice_nano.uf2` from the `corne-prospector` artifact
first (then double-tap reset again and flash the real firmware) to clear
stale bonds.

## Keymap

The keymap matches `corne-prospector/config/corne.keymap` so both configs
share muscle memory. The only delta: this build does not include
`&studio_unlock` (use the `corne_left_with_studio` variant for live
editing).
