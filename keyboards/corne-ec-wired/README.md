# Corne — electro-capacitive, wired

46-key Corne with electro-capacitive switches, wired. USB `0022:45d3`, reports as `corne_ec`.

Firmware: **Vial** (protocol 6, QMK >= 0.19 keycodes), 8x7 matrix, 8 layers, 64 combo slots.
Custom keycodes: `EC_AP_I` (0x7E00, actuation point up), `EC_AP_D` (0x7E01, down),
`EC_CLR` (0x7E02, reset EC config).

## Keymap

Programmed live from the canonical layout — don't edit it in Vial and expect it to stick
across syncs:

```sh
cd shared/layout
python3 -m kbsync.cli push corne-ec --dry-run   # show changes
python3 -m kbsync.cli push corne-ec             # back up, write, read back and verify
python3 -m kbsync.cli restore corne-ec ../../keyboards/corne-ec-wired/backups/<file>.json
```

Board profile: [`shared/layout/boards/corne-ec.yaml`](../../shared/layout/boards/corne-ec.yaml)
(matrix map, inner-column keys, Function-layer overrides: `QK_BOOT`, `EC_AP_D`, `EC_AP_I`, `EC_CLR`).

`backups/` holds a snapshot taken before every push. `vial-definition.json` is the board's
Vial definition (matrix + KLE layout).

## Not available on this firmware

- **Globe** — stock QMK has no keycode for consumer usage 0x29D; needs a custom keycode
  and a firmware rebuild. The inner bottom-left key is `KC_NO` until then.
- Bluetooth / Studio unlock keys, absolute brightness (0x71), mic keys (0x04, 0xD5) → `KC_NO`.
