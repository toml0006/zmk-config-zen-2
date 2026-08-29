# DASBOB Flashing

36-key diodeless split choc keyboard ([GroooveBob/DASBOB](https://github.com/GroooveBob/DASBOB)).
Sold pre-soldered by [beekeeb](https://docs.beekeeb.com/dasbob-keyboard).

## ⚠️ Controller requirement: RP2040 (wired) or nRF52840 (wireless)

DASBOB is **diodeless** — every key wires direct to its own MCU pin (~18/half).
The PCB has **no diodes**, so a matrix scan is impossible; direct pins are mandatory,
and the layout uses **extra pins beyond a standard Pro Micro** (Elite-C pinout).

The board is **dual-mode** — its Pro-Micro-form footprint (note the `nice` silkscreen,
battery pads, and power-switch pads) accepts either:

- **Wired** → an **RP2040** with extra pins (Sea-Picro EXT / Helios) — this guide's main path.
- **Wireless** → an **nRF52840** in the nice!nano footprint + battery + ZMK. See
  [Wireless](#wireless).

Either way the controller must expose the diodeless **extra pins**.

**ATmega32U4 Pro Micro / Arduino Micro boards do NOT work** — too few pins, and no
AVR firmware exists (QMK/KMK/VIAL are RP2040 builds; ZMK is the nRF52840/wireless
path). USB ID `0x2341/0x8037` = ATmega32U4 → wrong board.

**A plain Pro Micro footprint is NOT enough either** — DASBOB's diodeless design
uses extra pads beyond the standard 21-pin Pro Micro layout, so the controller must
expose those (Elite-C pinout = Pro Micro + 5 extra pins at the USB end). See
[Which controller to buy](#which-controller-to-buy).

## Which controller to buy

DASBOB needs an **RP2040 board with the Elite-C pinout** (Pro Micro footprint **+ 5
extra pins** at the USB end). The diodeless PCB wires keys to those extra pins —
a normal 21-pin Pro Micro can't reach them.

| Controller | Buy it? | Notes |
|---|---|---|
| **Sea-Picro EXT** | ✅ **Best** | Elite-C pinout, 16MB flash. The board beekeeb sells *for* DASBOB. Get the **EXT** variant (Elite-C pinout + 5 extra pads). [beekeeb](https://shop.beekeeb.com/products/sea-picro) |
| Helios (0xCB) RP2040 | ✅ | Elite-C-pinout RP2040, works for diodeless. |
| Elite-Pi (keeb.io) | ✅ | Elite-C pinout RP2040 — has the 5 extra pins. |
| Sea-Picro **RST** | ⚠️ avoid | Uses the end space for a reset button instead of the 5 extra pins → may not reach DASBOB's diodeless pads. Get EXT, not RST. |
| KB2040 / RP2040 Pro Micro / RP2040-Zero | ❌ | Plain Pro Micro / non-standard pinout — **missing the extra diodeless pins.** |
| Any ATmega32U4 (Pro Micro, Elite-C AVR) | ❌ | Wrong MCU. No firmware, too few pins. |

Buy **two** (one per half). Rule of thumb: **"RP2040 + Elite-C pinout + extra pins."**

## Firmware

`dasbob_vial_rp2040.uf2` — official beekeeb VIAL build for RP2040 (verified UF2,
familyID `0xe48bff56`, 186 blocks / 95232 bytes).

- Source: <https://docs.beekeeb.com/dasbob-keyboard> (short link `https://s.beekeeb.com/dasbobvial`)
- VIAL = live remapping via the [VIAL app](https://get.vial.today) (no rebuild needed).
- QMK-default alternative (static keymap): build from <https://github.com/GroooveBob/DASBOB-qmk>
  (`make dasbob:default`). Note: the fork is stale vs current QMK — expect toolchain
  fixups. VIAL uf2 is the easy path.

## Flash steps (per half — same uf2 on both)

1. Plug ONE half into USB.
2. Enter bootloader → `RPI-RP2` drive mounts:
   - **Blank RP2040**: boots straight to BOOTSEL, drive appears on plug-in.
   - **Has firmware**: double-tap RST, OR hold BOOT while plugging in, OR short
     the BOOT pad to GND while tapping RST.
3. Copy firmware onto the drive — it flashes and reboots automatically:
   ```sh
   cp dasbob_vial_rp2040.uf2 /Volumes/RPI-RP2/
   ```
   (macOS may report an eject error as the drive disconnects mid-write — normal.)
4. Repeat for the other half.

Handedness is automatic (master = whichever half holds USB). Verify in the VIAL app:
keyboard shows up as **DASBOB**.

## Wireless

The PCB is wireless-ready: nice!nano-footprint pads, a **battery** (LiPo) hookup, and a
**power switch**. Wireless runs on an **nRF52840** controller with **ZMK** firmware
(Bluetooth LE; split halves talk over BLE, so no TRRS/serial wire between them).

### Controller — pins

DASBOB diodeless needs **18 GPIO/half + the 3 extra pins** (`P1.01/02/07`). Wireless
split is BLE, so **no inter-half serial pin** is needed. Every nRF52840 board *has* those
pins — what differs is **where** they sit (see the alignment note below):

| Wireless controller | Buy? | Notes |
|---|---|---|
| **Genuine nice!nano v2** | ✅ drop-in | **21 usable GPIO** = 18 edge + **3 extra inner pads** `P1.01 / P1.02 / P1.07` (mid-board). Those 3 are the diodeless extras, and they sit **exactly where DASBOB routes them**. Solder the 3 inner pads; done. The `nice` silkscreen targets this board. |
| 1:1 nice!nano clone | ✅ verify layout | Fine **only if** the 3 extras are **mid-board** like the real thing (see alignment note). |
| **SuperMini nRF52840** / generic USB-C+charging clones (e.g. AITRIP) | ⚠️ jumpers | Has `P1.01/02/07`, but **relocated to their own pins** (near USB-C) — **not at nice!nano positions**, so they **don't line up with DASBOB's inner pads**. Needs **3 jumper wires**. [Keebio](https://keeb.io/products/supermini-nrf52840-pro-micro-bluetooth-le-ble-controller) |
| nRFMicro | ⚠️ verify | nRF52840 Pro-Micro form; confirm it breaks out the 3 extras at usable positions. |

Verified nice!nano v2 pin count: 18 edge + 3 inner (`P1.01/02/07`) = 21 usable GPIO
([nicekeyboards pinout](https://nicekeyboards.com/docs/nice-nano/pinout-schematic/)).

#### ⚠️ Pad-alignment matters (clone gotcha)

DASBOB routes its 3 diodeless extras to the **nice!nano inner-pad positions** (mid-board)
— that's what senz's shield (`&gpio1 1/2/7`) and the `nice` silkscreen assume. So the
*physical location* of `P1.01/02/07` on the controller decides drop-in vs rework:

- **3 extra pads in the MIDDLE** of the board (between the pin rows) → true nice!nano
  layout → **drop-in.**
- **3 extras clustered at the BOTTOM by the USB-C** → SuperMini layout → relocated,
  **not nice!nano-compatible** → **run 3 jumper wires** from those pins to DASBOB's inner
  pads. Same ZMK firmware, just extra wiring.

5-second check before buying/soldering: **look at where the 3 extra pads are.** Generic
USB-C charging clones (AITRIP etc.) are almost always SuperMini layout → jumpers.
For true drop-in, buy a **genuine nice!nano v2** — or skip all this and go wired
**Sea-Picro EXT**.

> Note: this is the opposite of a **Corne**, which is a diode matrix and uses **none** of
> `P1.01/02/07` — there any nice!nano/SuperMini clone is pin-fine (watch only physical
> fit). DASBOB's diodeless design is what makes pad alignment matter.

### Firmware — ZMK (community shield, no official prebuilt)

- GroooveBob marks DASBOB ZMK **"Not tested"** and ships **no prebuilt wireless uf2**.
  But a working **community shield exists** — reuse it instead of writing one.
- **[senz/zmk-config](https://github.com/senz/zmk-config)** — proven DASBOB-on-nice!nano build:
  - `build.yaml`: `board: nice_nano_v2`, `shield: dasbob_left` / `dasbob_right`.
  - Shield at `config/boards/shields/dasbob/` (`dasbob.dtsi`, `dasbob_{left,right}.overlay`,
    `Kconfig.*`, `dasbob.zmk.yml`). Keymap: `config/dasbob.keymap`.
  - `kscan` = `zmk,kscan-gpio-direct`, **18 direct pins/half** (diodeless). 15 on
    `&pro_micro` pins + **3 on nice!nano's inner extras**: `&gpio1 1/2/7` = **P1.01/02/07**.
    → confirms a **bare nice!nano v2 works** (solder those 3 inner pads).
  - Pinned to **ZMK v0.2.1** (old) — bump the `west.yml` revision if you want current ZMK.
  - No display configured in this shield (no nice!view/OLED in the dasbob build).
- Fastest route: fork senz's repo, edit `config/dasbob.keymap`, let GitHub Actions build
  `dasbob_left`/`dasbob_right` uf2 artifacts. Or [build your own](https://zmk.dev/docs/user-setup).
- Flashing ZMK = same UF2 drag-drop as below; nice!nano's bootloader drive mounts as
  `NICENANO`. One uf2 per half (left/right are different builds here).

### Also need

- LiPo battery (e.g. 110–301230 mAh, JST or solder pads per the PCB).
- The power switch (if not pre-populated).
- Optional nice!view display instead of the SSD1306 OLED for low-power wireless.

### If wireless is the real goal

DASBOB-wireless is a DIY/untested firmware path. For a turnkey wireless choc split,
a board designed around nice!nano + ZMK is far less work — e.g. **Totem** (already in
this repo at `../zmk-totem/`), Corne, or Ferris/Sweep.

## Buzzer & haptic

### Buzzer — supported (optional)

DASBOB has an **optional passive piezo buzzer** footprint, driven by MCU PWM
(`AUDIO_PIN GP5`, `AUDIO_CLICKY`). Use a **passive** 2-pin piezo — NOT a self-oscillating
"active" buzzer (that gives one fixed beep, no songs/clicky). ~5V, the footprint is 11×9mm.

- [KeebSupply Piezo Buzzer](https://keeb.supply/products/piezo-buzzer) — keyboard-sized, best fit
- [Keebio Piezo Speaker](https://keeb.io/products/piezo-speaker)
- [Adafruit PS1240](https://www.adafruit.com/product/160) — classic 12mm THT passive piezo (~4kHz, matches DASBOB's 4.1kHz)

Not included in beekeeb kits. On wireless (ZMK), audio support trails QMK — buzzer is the
dependable feedback there.

### Haptic — NOT supported

No haptic on DASBOB: no driver-IC pads, no motor footprint, no `HAPTIC_ENABLE` in firmware
(only `AUDIO`). Adding it is a real mod (driver IC + motor + free GPIO + custom QMK):

- Driver: [DRV2605L breakout](https://www.adafruit.com/product/2305) (I²C)
- Motor: [LRA](https://www.adafruit.com/product/1201) (crisper than ERM), or any 10mm coin LRA/ERM
- Wire to free I²C pins, set QMK `HAPTIC_ENABLE = yes` + `HAPTIC_DRIVER = drv2605l`, rebuild.
  Only realistic on the **wired RP2040** path (spare pins); ZMK haptic is limited.

## Quick verify drive is present (macOS)

```sh
ls /Volumes/RPI-RP2 && cat /Volumes/RPI-RP2/INFO_UF2.TXT
```
