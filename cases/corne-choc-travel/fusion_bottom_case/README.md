# corne_bottom_case

Parametric rebuild of the Typeractive Corne Choc **bottom case**, as native
Fusion features. Built for editing the wall cutouts.

## Why a rebuild and not a conversion

Two conversion routes were tried first and both are dead ends:

| Route | Result |
|---|---|
| Fusion `Mesh -> Convert -> Prismatic` | `RuntimeError: 3 : No rights for mesh conversion` — the method setter is subscription-gated. Faceted is the only ungated method, and faceted means one B-Rep face per triangle. |
| FreeCAD `makeShapeFromMesh` (`../stl_to_step.py`) | Valid solid, but **2078 faces for a 2078-triangle STL**. Every flat wall is hundreds of coplanar triangles, so no face can be push/pulled and no edge takes a fillet. `removeSplitter()` only merges 2078 → 1800, because the mesh is meshopt-quantized to a 0.0081 mm grid and "flat" regions are not exactly coplanar. |
| Offline plane-merging (attempted) | 1176 faces, 247 groups unclosed, shell invalid. Capped out because ~1370 of the 2078 facets are genuine corner radii — the top 50 surfaces hold 95.1% of the area, the rest is curvature that plane-fitting cannot clean up. |

The rebuild gives **189 faces** instead of 2078, all analytic, with a real
timeline.

## What the part actually is

Measured off `case-bottom-3dp-meshopt.stl`:

- a **1.5 mm uniform shelled tray** — one outline extruded 10.43 mm, shelled
  with the underside removed
- plate from Y 2.034 to 3.532; skirt down to Y −6.90; a rib on the +X side
  down to Y −12.965
- 5 screw holes, Ø2.47 mm
- 2 wall openings

The 1.5 mm figure is not a guess. A 1.5 mm inward offset of the outline
predicts a skirt band of 601.8 mm²; the slice at Y=−2.0 measures 577.9 mm².
The 23.9 mm² difference is exactly the USB port (16.0 wide × 1.5 wall)
passing through that slice.

## Verification

`verify_rebuild.py` rebuilds the same solid in FreeCAD and checks it:

```
rebuild : vol 19261.1 mm3  faces 189  edges 559  valid True
mesh    : vol 19187.7 mm3  ->  delta +73.4 mm3 (+0.38%)
bbox    : X -134.97..-2.09  Y -12.96..3.53  Z -37.18..50.98
mesh    : X -134.99..-2.09  Y -12.97..3.53  Z -37.19..51.00
```

Bounding box matches within 0.02 mm on every axis. The +0.38% volume is the
top-edge chamfer and corner radii, which this prismatic rebuild does not
model — add them as Fusion fillets if you want them.

## Run

Fusion → `Utilities` → `Add-Ins` → `Scripts and Add-Ins` (`Shift + S`) →
`My Scripts` → `corne_bottom_case` → `Run`.

### How it is installed

`API/Scripts/corne_bottom_case/` is a **real folder** holding a small
launcher shim, not a symlink to this repo. Two reasons:

- Fusion does not reliably follow symlinked script folders.
- The manifest must say `"autodeskProduct": "Fusion"`. The renamed *Autodesk
  Fusion* build filters out entries that still say `"Fusion360"`, which makes
  a script look listed but do nothing when run.

The shim loads `corne_bottom_case.py` from this repo by absolute path and
re-executes it every run, so this folder stays the source of truth and edits
apply immediately — including edits to `CUTOUTS`.

### If nothing happens

The script always ends in a dialog, success or failure, so silence means it
never loaded. Check, in order:

1. `View` → `Show Text Commands`. Every step logs a `[corne_bottom_case]`
   line; the last one tells you how far it got.
2. Confirm `corne_bottom_case` is listed under `My Scripts`. If not, click
   `+` and select `API/Scripts/corne_bottom_case`.
3. Confirm the manifest says `"autodeskProduct": "Fusion"`.

Or skip scripting entirely and open `corne_bottom_case.step`.

Prefer to skip Fusion scripting? `corne_bottom_case.step` in this folder is
the verified solid — just `File` → `Open` it. STEP import is not
license-gated.

## Orientation

The STL is authored with the floor plate at the **top**, so the part arrives
upside down. The Fusion script maps

```
Fusion X = mesh X        Fusion Y = mesh Z        Fusion Z = plate_top - mesh Y
```

which stands the case on its floor at `z = 0`.

That negation is not only cosmetic. The earlier mapping simply swapped the
mesh Y and Z axes onto Fusion Z and Y, and a bare axis swap has determinant
**-1** — so the body in Fusion was a *mirror image* of the STL, not a rotation
of it. On an asymmetric Corne half that is a real defect. Negating one axis
restores determinant +1.

Heights in the corrected frame, at `case_extra_height = 0`:

| feature | z |
|---|---|
| floor | 0.000 … 1.498 |
| `usb_port` | 3.792 … 7.692 |
| `side_port` | 6.932 … 10.432 |
| rim (open top edge) | 10.432 |
| rib top | 16.497 |

`verify_rebuild.py` still works in the original mesh frame, since that is what
the source STL is measured in. Same geometry, different labels.

## Raising the rib: `case_extra_height`

The script creates one Fusion **user parameter**, `case_extra_height`,
default `0 mm`. After the first run it lives in `Modify` → `Change
Parameters`, so you can change it there and the model rebuilds — no need to
re-run the script.

It raises **only the rib** — the L-shaped taller wall run at the +X end,
`RIB_OUTLINE`. The floor, the main perimeter wall and the screw holes do not
move.

Both openings lie inside the rib's footprint in plan:

| opening | wall | plan extent | inside rib? |
|---|---|---|---|
| `side_port` | +Z | X −19.5…−8.5 | rib's top segment |
| `usb_port` | +X | Z −6.0…10.0 | rib's vertical segment |

so they travel up with it, keeping a constant distance below the rib's top
edge.

Measured, as the verifier reports in the mesh frame:

| | 0 mm | 3 mm |
|---|---|---|
| `usb_port` gap to rib end | 6.065 | **6.065** |
| `side_port` gap to rib end | 3.325 | **3.325** |
| rib end | −12.965 | **−15.965** |
| floor / perimeter rim | unchanged | unchanged |
| volume | 19261.0 mm³ | 19616.4 mm³ |

The volume rise of **+355.4 mm³** is the rib band area (118.6 mm²) × 3. That
is the check that the scope is right: raising the whole perimeter would use
the outline band (601.8 mm²) and add ~1801 mm³ instead.

To check a value without opening Fusion:

```
EXTRA_HEIGHT=3 /Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd verify_rebuild.py
```

## Stiffening

This part is an **open** thin-walled section — a tray with no top. Open
sections resist torsion by St. Venant warping, `J ≈ ⅓Σbt³`, which is feeble.
A closed section resists by shear flow, Bredt's `J = 4A²/∮(ds/t)`.

For this geometry (mean section 67.6 mm wide, 10.43 mm walls, PLA-ish
G ≈ 1300 MPa):

| configuration | J (mm⁴) | vs as-built | twist per N·m |
|---|---|---|---|
| open tray, t=1.5 (as built) | 99.5 | 1.0× | 59.0° |
| open tray, t=2.0 | 235.8 | 2.4× | 24.9° |
| open tray, t=2.4 | 407.5 | 4.1× | 14.4° |
| open tray, t=3.0 | 795.9 | 8.0× | 7.4° |
| **closed box, t=1.5** | **13931** | **140×** | **0.42°** |

Closing the top dwarfs everything else. Doubling the wall to 3 mm buys 8× for
8× the wall material; a working shear panel across the opening buys ~140×,
and even a 25%-effective one buys ~36×.

These are first-order thin-walled estimates (St. Venant open, Bredt closed).
They ignore the rib, the port cutouts and end effects, so treat them as
ratios rather than absolute predictions. The 140:1 conclusion is structural
and robust to all of that.

### What the script implements

| knob | default | effect |
|---|---|---|
| `FILLET_RADIUS_MM` | 2.0 | fillets the inside floor-to-wall junction |
| `wall_thickness` (Fusion parameter) | 1.5 | shell thickness; J scales with t³ |

**Fillet.** The floor-to-wall corner is where the U-channel hinges. In pure
thin-walled theory a junction fillet adds only modestly to `J`; its real value
is cutting the stress concentration and the local hinging compliance at that
corner. Cheap, no clearance cost. The script retries at decreasing radii and
logs a skip if the geometry will not take it.

**Wall thickness.** Now a live Fusion parameter, so you can try 2.0 or 2.4 in
`Change Parameters` and check fit before committing.
**The shell grows inward, so raising it shrinks the cavity by the same amount
per side.** Verify the PCB and plate still drop in before printing.

### Not done: closing the section

The PCB bolts to the five holes in the floor, so it already acts as a partial
shear panel. What limits it is that those holes sit well inboard, so the wall
can only reach a screw by bending the floor across the gap:

| screw hole (x, z) | distance to nearest wall |
|---|---|
| (−113.769, 7.730) | 19.44 mm |
| (−113.769, 24.731) | 19.23 mm |
| (−72.867, −6.970) | 7.31 mm |
| (−41.773, 28.133) | 18.18 mm |
| (−28.365, −13.571) | 16.58 mm |

Mean 16.1 mm, and 5 fasteners on a 405 mm perimeter is ~81 mm spacing.

Bosses at those positions webbed out to the nearest wall were tried and
removed (they cost ~1947 mm³ and assumed a plate height this model cannot
confirm). If the twist ever needs addressing again, the options are:

- **bosses + webs** at the five existing holes, webbing each to the nearest
  point on `PLATE_OUTLINE` to convert that floor-bending cantilever into a
  shear web. Needs the real spacer length to set the boss height;
- **an internal ledge** at plate height, capturing the plate laterally around
  the full perimeter. No fasteners and no PCB changes; needs the plate outline;
- **a diagonal brace** across the opening, if the top must stay open.
  Diagonals load in tension/compression rather than bending.

### A note on the reference PCB

`../reference_corne-chocolate.kicad_pcb` is the **panelized foostan crkbd**,
pulled in only to trace the outline. It is not the Typeractive board. It has
no `MountingHole` footprints; its Ø5.00 mm `Edge.Cuts` circles are controller
cutouts, and its only M2-sized (r=1.000) arcs sit at x = ±137.6, the panel
edges — tooling holes. Neither set matches this case's five holes (pairwise
distance error 99.7 mm and 114.1 mm respectively).

Do not use that file to place mounting features. The five positions in
`SCREW_HOLES` were measured from the Typeractive STL and are correct.

## Editing cutouts

Edit `CUTOUTS` in `typeractive_bottom_profile.py` and re-run:

```python
CUTOUTS = [
    dict(name='usb_port',  wall='+X', at=  -2.087, along=  1.960,
         width=16.00, y=-2.21, height=3.90),
    dict(name='side_port', wall='+Z', at=  45.500, along=-13.990,
         width=10.95, y=-5.15, height=3.50),
]
```

| Field | Meaning |
|---|---|
| `wall` | which wall: `'+X'`, `'-X'`, `'+Z'`, `'-Z'` |
| `at` | position of that wall along its normal axis |
| `along` | centre of the opening along the wall |
| `width` | opening size along the wall |
| `y` | centre height (STL frame, +Y up) |
| `height` | opening height |

Raising `y` moves a port up — the thing `../shift_cutouts.py` was doing by
boolean surgery on the faceted STEP, now a one-number edit. Its `DY_SHIFT =
2.33` becomes `y=-2.21 + 2.33`.

Cutouts are cut symmetrically about the wall plane, so they always cut
through regardless of which way the construction plane faces.

After editing, re-run `verify_rebuild.py` to confirm the solid still closes
before opening Fusion.

## Coordinates

All numbers are in the STL's native frame, so they match the `.step` files
and `../shift_cutouts.py`:

```
X = case length      Z = case depth      Y = height (+Y up)
```

The Fusion script maps mesh (X, Z, Y) → Fusion (X, Y, Z). That is an axis
relabel only; no number changes.

## Files

| File | What |
|---|---|
| `corne_bottom_case.py` | the Fusion script |
| `typeractive_bottom_profile.py` | **generated** profile data + `CUTOUTS` |
| `extract_profile.py` | regenerates the above from the STL (needs trimesh + shapely) |
| `verify_rebuild.py` | FreeCAD rebuild + volume/bbox check, writes the STEP |
| `corne_bottom_case.step` | verified analytic B-Rep, 189 faces |

## Not modelled

Top-edge chamfer, corner radii, and any draft on the skirt. Add as Fusion
fillets/chamfers after the build if you need them.
