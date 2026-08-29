# Corneish Zen v2 ZMK config

ZMK config for the **Corneish Zen v2** (LOWPROKB low-profile wireless
split). Lives in the [keyboard monorepo](../README.md).

V2 PCBs ship in the 3rd group-buy round (R3) — V2 PCBs have white power
switches, V1 PCBs have black ones. For V1, uncomment the appropriate
lines in `build.yaml` instead.

## Layout

```
corneish-zen-v2/
  build.yaml                       Left/right + a left-with-Studio variant
  config/
    west.yml                       ZMK main
    corneish_zen_mod.conf
    corneish_zen_mod.keymap        4 layers (QWERTY / NUMBER / SYMBOL / FN)
```

The custom Corneish Zen boards live at
[`../boards/lowprokb/corneish_zen_mod/`](../boards/lowprokb/corneish_zen_mod/)
(shared board_root for the monorepo, registered in the root
`zephyr/module.yml`).

## Building

Push to `main` — the [monorepo workflow](../.github/workflows/build.yml)
builds this config and uploads `corneish-zen-v2.zip` as an Actions
artifact. The archive contains the left and right firmware plus a
`corneish_zen_v2_left_with_studio` variant for live editing via
[ZMK Studio](https://zmk.studio).

## Flashing

Double-tap reset on a half → it mounts → drag the matching `.uf2`. If you
only changed the keymap, you usually only need to reflash the **left**
half (it's the split central and owns the keymap).

## Resources

- [ZMK Firmware](https://github.com/zmkfirmware/zmk)
- [ZMK Docs](https://zmk.dev/docs)
- [Corneish Zen upstream](https://github.com/lowprokb/zmk-config-zen-2)
