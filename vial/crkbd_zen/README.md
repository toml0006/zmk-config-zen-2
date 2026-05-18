# crkbd_zen — Vial keymap (Corne equivalent of the Cornish Zen ZMK config)

This is a **QMK/Vial** keymap for a standard wired Corne (`crkbd`) that mirrors the
ZMK keymap in `config/corneish_zen_mod.keymap`. The Cornish Zen itself runs ZMK
and cannot use this — flash these onto a separate Corne board running Vial-QMK.

## What's translated

| ZMK | QMK/Vial |
| --- | --- |
| `&kp X` | `KC_X` |
| `&mt LALT ESC` | `MT(MOD_LALT, KC_ESC)` |
| `&mo 1` / `&mo 2` | `MO(_LOWER)` / `MO(_RAISE)` |
| `&kp LG(GRAVE)` | `G(KC_GRV)` |
| `&kp LG(LS(LBKT))` | `S(G(KC_LBRC))` |
| `&kp LS(LG(N4))` | `S(G(KC_4))` |
| `&kp LC(LS(LG(N4)))` | `C(S(G(KC_4)))` |
| conditional layer (1+2 → 3) | `update_tri_layer_state(state, _LOWER, _RAISE, _FN)` |

## What's gone

- **Bluetooth keys** (`&bt BT_SEL 0..4`, `&bt BT_CLR`) — replaced with `KC_NO`
  on the lower layer, and `KC_TRNS` on the FN layer.

## Build & flash

1. Clone Vial-QMK: `git clone https://github.com/vial-kb/vial-qmk.git`
2. Copy this folder into the keyboard's keymaps directory:
   ```
   cp -r vial/crkbd_zen <vial-qmk>/keyboards/crkbd/rev1/keymaps/
   ```
3. Compile and flash (replace `:flash` with `:dfu`/`:avrdude` as appropriate):
   ```
   qmk compile -kb crkbd/rev1 -km crkbd_zen
   qmk flash -kb crkbd/rev1 -km crkbd_zen
   ```
4. Open the [Vial GUI](https://get.vial.today/) — the keymap is editable
   live at runtime. The unlock combo is the two outermost top-row keys
   (top-left `TAB` and top-right `BSPC`), held simultaneously.

## Notes

- `VIAL_KEYBOARD_UID` is randomized in `config.h`. If you flash multiple Vial
  boards, regenerate with `python3 -m util.vial_generate_keyboard_uid` from
  vial-qmk and replace the value.
- `TAPPING_TERM` is 200 ms — tweak in `config.h` if `MT(MOD_LALT, KC_ESC)`
  feels too eager or too sluggish.
- The `vial.json` layout shipped with Vial-QMK's stock `crkbd` Vial keymap
  works as-is; no need to provide one here.
