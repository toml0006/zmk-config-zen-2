# Corne-ish Zen V2 — Community Notes

Research snapshot of mods, switches, caps, and resources the community runs on
this board. Collected 2026-04-11.

## Switches (Kailh Choc v1 — v2 is NOT compatible)

The Zen uses Choc v1 hotswap sockets. Choc v2 has a different center post and
won't seat in v1 sockets — ignore anything v2.

| Switch | Type | Weight | Notes |
|---|---|---|---|
| Kailh Choc Pro Red | Linear | 35g | Most common "just works" linear, smoother than original Choc Red |
| Kailh Choc Pro Pink | Linear | 20g | Ultralight, popular with topre/silent-tactile refugees |
| Kailh Choc Sunset | Tactile | ~50g | Current go-to tactile, pronounced bump, not scratchy |
| Gateron gChoc (low profile) | Linear | 20g | Evan Travers' pick — see build notes below. Hard to source |
| Kailh Choc White / Red (original) | Linear | 20g / 50g | Still around, cheaper, most people upgrade to the Pro line |

**Silencing:** a lot of people add tempo tape or dampening foam under the PCB
since the Zen's aluminum case rings a bit.

## Keycaps

- **MBK Choc** (FKcaps) — default recommendation. Cheap, uniform profile, good
  texture. Most Zen build photos use these.
- **KLP Lamé** — sculpted, much more tactile row differentiation. Community
  print files at `braindefender/KLP-Lame-Keycaps` on GitHub. (This is what I
  print on the H2D / Monoprice SLA.)
- **Chocfox CFX** — sculpted MT3-style for Choc. Premium feel, $$$, scarce.
- **Chicago Steno** (Asymplex) — flat, minimal, popular with typing nerds. Used
  in the evantravers.com Zen review.
- **Osume / Cerakey ceramic** — niche but a few Zen owners run ceramic Choc
  caps for the feel.

## Mods

- **Tenting** — stock Zen is flat. People 3D print tenting feet or buy
  Dygma-style adjustable tent legs. Thingiverse/Printables has several models
  sized to the Zen's case screws.
- **Tripod mounts** — epoxy a 1/4-20 nut into each half's bottom so it mounts
  on a mini tripod for fully adjustable tent + splay. Classic ergo-board mod.
- **Silicone feet** — stock feet slide; swap for bigger silicone bumpons.
- **Display mods** — most forks of the custom_status_screen just swap the
  logo. My build (battery via BQ274xx, device name, WPM, rotating pixel art,
  etc.) is well past where most stop.
- **Battery swap** — stock 180 mAh is fine but some people solder in 301230 or
  402030 cells for multi-month runtime. Trade-off is case fit.
- **Case material** — a few builds use wood-fill PLA or resin top plates for
  aesthetics.

## Keymap references worth stealing from

- **urob/zmk-config** — canonical homerow-mods reference. Excellent timeout
  tuning, combos, smart layers. Most serious ZMK configs cite this.
- **Townk/zmk-config** — clean Corne layout, good layer organization.
- **LOWPROKB/zmk-config-zen-2** — vendor's own reference config for V2 (what
  my board started from).
- **caksoylar/keymap-drawer** — not a keymap but the SVG renderer everyone
  uses for READMEs.
- **KeymapDB** (keymapdb.com) — searchable collection of Corne/36-key layouts.

## Community hubs

- **ZMK Discord** — `#hardware-lowprokb` and general `#help`. Most active
  place for Zen-specific questions.
- **r/ErgoMechKeyboards** — active again, lots of Zen build logs.
- **geekhack.org** — the original LOWPROKB Zen thread has build pics and
  troubleshooting history.
- **lemmy.ml / lemmy.world** ergomech communities — smaller but quality.

## Notable individual builds

- **evantravers.com** "Corne-ish Zen" post — gChoc 20g + Chicago Steno, heavily
  tuned homerow mods, good photos.
- Mastodon `#ergomech` tag — periodic posts with wood-grain resin cases, brass
  tenting feet, etc.

## Monoprice Mini SLA notes (for keycap printing)

- The Mini SLA is a **rebadged Malyan S100**, not an AnyCubic Photon. It reads
  **`.cws`** files (CreationWorkshop format).
- Recommended slicer: **Slic3r SLA Edition** (Prusa Slic3r fork from Monoprice/
  Malyan). Has the S100 profile preloaded. CreationWorkshop also works.
- ChiTuBox can export `.cws` but has no first-class S100 profile.
- Malyan wiki: `slawiki.malyansys.com`.

## Hardware gotchas learned the hard way

- Upstream ZMK's V2 overlay **wrongly** uses a voltage divider for battery.
  The V2 actually has a BQ274xx fuel gauge (same as V1). Use I2C1 (not I2C0,
  which conflicts with SPI0 for the display).
  - Left: SDA=P0.06, SCL=P0.26, INT=P1.14
  - Right: SDA=P0.16, SCL=P0.13, INT=P1.05
- LVGL `lv_image_set_scale` is a no-op on 1-bit indexed images — pre-scale in
  Python.
- BLE device name limit is 16 chars ("Corne-ish Zen Mod" = 17, rejected).
- WPM widget is central-only; `zmk_keycode_state_changed` is not linked on the
  peripheral build.
- Modifier indicators on e-paper are worse than useless — refresh lag means
  the glyph appears after the key is released.
