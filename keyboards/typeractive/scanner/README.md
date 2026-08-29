# Corne + Prospector Scanner ZMK config

Standalone Corne (left = central, right = peripheral) + a **passive
Prospector Scanner**. The keyboard works fully on its own; the scanner
listens to BLE status advertisements and renders them without ever
joining the split. Lives in the [keyboard monorepo](../README.md);
contrast with [`../corne-prospector/`](../corne-prospector/) (dongle =
central, keyboard depends on it).

## Topology

| Device              | Board                  | Shield                                    | Role |
| ------------------- | ---------------------- | ----------------------------------------- | ---- |
| Corne left half     | `nice_nano@2.0.0//zmk` | `corne_left nice_view_adapter nice_view`  | split central + broadcaster |
| Corne right half    | `nice_nano@2.0.0//zmk` | `corne_right nice_view_adapter nice_view` | split peripheral |
| Prospector Scanner  | `xiao_ble//zmk`        | `prospector_scanner`                      | passive observer (no BLE link) |

The scanner is **not** part of the split. Unplug or move it; the keyboard
keeps working. The keyboard side runs the **t-ogura fork** of the
Prospector module (`v2.2.1`), which adds the broadcaster
(`CONFIG_ZMK_STATUS_ADVERTISEMENT=y`) and the `prospector_scanner` shield.

## Layout

```
corne-scanner/
  build.yaml                         4 build targets
  config/
    west.yml                         ZMK main + t-ogura/prospector-zmk-module @ v2.2.1
    corne.keymap                     W-CORNE keymap (same as corne-standalone)
    corne_left.conf                  central + broadcaster + display
    corne_right.conf                 peripheral + display
    prospector_scanner.conf          scanner — non-touch (display only)
    prospector_scanner_touch.conf    scanner — touch override (CST816S)
```

## Channel

The broadcaster uses `CONFIG_PROSPECTOR_CHANNEL=1` in
`corne_left.conf` and the scanner filters on
`CONFIG_PROSPECTOR_SCANNER_CHANNEL=1`. Change both together if you want a
different channel (1-9 selectable, 0 = scanner receives all).

## Building

Push to `main` — the [monorepo workflow](../.github/workflows/build.yml)
builds this config and uploads `corne-scanner.zip`:

- `corne_left-nice_nano@2.0.0__zmk-zmk.uf2` / `corne_right-...uf2`
- `prospector_scanner.uf2` — non-touch
- `prospector_scanner_touch.uf2` — touch variant (flash either one)

## Flashing

Double-tap reset on each device → drag the matching `.uf2` onto the
mount. Order does not matter — the scanner has no pairing relationship.

If you switch from another Corne config (`corne-prospector` or
`corne-standalone`) the BLE roles change. Wipe bonds first using the
`settings_reset_nice_nano.uf2` from the `corne-prospector` artifact, then
flash the real firmware.

## Switching scanner layouts at runtime

In **non-touch** builds, layout is fixed at compile time via
`CONFIG_PROSPECTOR_DEFAULT_LAYOUT` (0=YADS, 1=Field, 2=Operator, 3=Radii).
Add to `prospector_scanner.conf` and rebuild.

In **touch** builds, swipe to change layout / channel / brightness on
the device — settings persist across reboots (NVS).

## Notes

- v2.2.1 fixes cold-boot peripheral connection on multi-peripheral splits
  ([t-ogura/zmk-config-prospector#20](https://github.com/t-ogura/zmk-config-prospector/issues/20))
- Default broadcast cadence is 1 Hz during typing with burst-on-change
  for layer / modifier / profile updates
