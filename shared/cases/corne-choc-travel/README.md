# Corne Choc Travel Case

Parametric Fusion 360 script that generates a 3D-printable travel case for the Corne Choc split keyboard.

- **Form-fit pockets** follow the Corne half outline (main key cluster + thumb-cluster bulge with chamfered transition).
- Each half is **rotated 90°** so the case ends up portrait-aligned and fits within a **250 × 250 mm** build plate.
- Right pocket is mirrored from the left, matching the physical layout.
- Lid included (with optional foam recess) and M3 corner bolt holes through both bodies.

## Default footprint

With the stock outline (118 × 92 mm half) rotated 90°:
- Pocket per half ≈ 92 × 118 mm (+ clearance)
- Tray ≈ **219 × 138 mm** (well under 250 × 250)

Script aborts with a clear error if the computed tray exceeds `build_plate`.

## Outline source

The default `half_outline_mm` was reconstructed from the **foostan/crkbd KiCad PCB** (`pcbs/corne-chocolate/hotswap/corne-chocolate.kicad_pcb`, `Edge.Cuts` layer). The source PCB is panelized — both halves plus a daughter board are joined on one piece by breakaway tabs — so the polygon is a clean reconstruction sized to the per-half bbox (~118 × 92 mm) observed in the panel.

Files saved for reference:
- `reference_corne-chocolate.kicad_pcb` — original KiCad PCB file
- `reference_pcb_outline.svg` — Edge.Cuts rendered to SVG
- `reference_pcb_loops.svg` — colored topological loops within the panel

**Verify with calipers against your physical PCB before printing.** The Keyboard Hoarders variant may use the v2, v3, or v4 PCB — outlines differ slightly between revisions.

## Run inside Fusion 360

1. `Utilities` → `Add-Ins` → `Scripts and Add-Ins` (`Shift + S`).
2. `My Scripts` → `+` → select this folder.
3. Highlight `corne_choc_travel_case` → `Run`.

New design opens with two bodies: `TrayBase` and `Lid` (lid offset in +Y for visibility — move/align for assembly).

## Tune dimensions

Edit `PARAMS` at the top of `corne_choc_travel_case.py` and re-run. Key params:

| Param | Default | Meaning |
|---|---|---|
| `half_outline_mm` | 6-point polygon | Corne half outline (natural orientation) |
| `pocket_clearance` | 1.5 mm | Per-side gap between pocket wall and PCB |
| `stack_height` | 22 mm | Plate + PCB + switches + caps |
| `rotation_deg` | 90° | CCW rotation applied to each half |
| `inner_gap` | 15 mm | Spacing between pockets |
| `border` | 10 mm | Outer wall thickness |
| `floor_thickness` | 4 mm | Tray floor below pocket |
| `lid_thickness` | 5 mm | Lid thickness |
| `lid_foam_depth` | 3 mm | Foam recess in lid (0 disables) |
| `corner_radius` | 8 mm | Outer corner fillet |
| `bolt_hole_dia` | 3.4 mm | M3 clearance |
| `bolt_hole_inset` | 6 mm | Corner hole inset |
| `build_plate` | (250, 250) | Hard sanity-check ceiling |

### Tuning the outline

If your PCB outline differs from the default:
1. Place the half face-down on graph paper or photograph against a ruler.
2. Trace clockwise from the top-INNER corner: top-inner → top-outer → bottom-outer of the main key area → diagonal into the thumb cluster → thumb cluster bottom → close to top-inner.
3. Replace `half_outline_mm`. Origin must be top-inner corner. +x toward the outer edge, +y down.

Outline must be a **simple closed polygon** (no self-intersection).

## Print + verify

- Print a small **2 mm test corner** of the pocket (slice just the pocket lip) to confirm clearance before printing the full tray.
- Adjust `pocket_clearance` if too tight (default 1.5 mm assumes a 0.4 mm nozzle + standard PLA shrinkage).

## Export for printing

`File` → `Export` → `STL` per body (`TrayBase`, `Lid`). Slice with 3–4 perimeters, 15–20% infill, 0.2 mm layer height.
