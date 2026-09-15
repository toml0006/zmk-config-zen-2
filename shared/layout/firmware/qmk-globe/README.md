# Globe key for QMK/Vial boards

Makes a Vial custom keycode send HID consumer usage **0x29D** (AC Next Keyboard
Layout Select), the same usage ZMK's `GLOBE` sends on the Corneish Zen.

Stock QMK/Vial can't do this live: no built-in keycode sends arbitrary consumer
usages and Vial macros only send keyboard-page keys. QMK's consumer report
descriptor covers 0x0000–0x02A0, so 0x29D fits once firmware sends it.

## Patch (add to the board's Vial keymap)

`keymap.c`:

```c
// Vial maps customKeycodes[i] in vial.json to QK_KB_0 + i.
// corne_ec already defines EC_AP_I, EC_AP_D, EC_CLR (QK_KB_0..2), so Globe is QK_KB_3.
#define KC_GLOBE QK_KB_3

bool process_record_user(uint16_t keycode, keyrecord_t *record) {
    if (keycode == KC_GLOBE) {
        host_consumer_send(record->event.pressed ? 0x29D : 0);
        return false;
    }
    return true;
}
```

`vial.json` — append to `customKeycodes` (after the existing entries, so the index matches):

```json
{"name": "GLOBE", "title": "Apple Globe (AC Next Keyboard Layout Select, 0x29D)", "shortName": "Globe"}
```

Requires `EXTRAKEY_ENABLE = yes` (already on if media keys work). If the board's
keyboard-level code already defines `process_record_user`, add the `if` block there.

## After flashing

Uncomment `qmk_keycodes: {globe: ...}` in the board profile (e.g.
`shared/layout/boards/corne-ec.yaml`) and run `kbsync push <board>`.

Caveat: releasing Globe sends an empty consumer report, which also releases any
media key held at the same moment.
