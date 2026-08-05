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

## The `case_extra_depth` parameter

A Fusion **user parameter** (`Modify` → `Change Parameters`), default `0 mm`.
Change it there and the model rebuilds — no need to re-run the script.

It lengthens the case upward from a fixed bottom, so **the extra height lands
entirely in the partial wall above the sidewall openings**. The openings, and
the wall below them, do not move.

| P | wall below | opening | wall above |
|---|---|---|---|
| 0 | 2.740 | 3.900 | 2.294 |
| 3 | 2.740 | 3.900 | 5.294 |

(`usb_port`. `verify_rebuild.py` prints this table for every opening.)

### What it drives

The main extrusion's height, and with it the plate-top construction plane and
the screw-hole cut depth. Those two must follow the top — holes sketched at
the old height would miss the plate.

The openings deliberately do **not** reference it. Their start offset is
measured from the fixed case bottom.

> Earlier this parameter was also added to each opening's height above the
> case bottom, on the reading that it should drive three operations. That is
> the opposite of what is wanted: it carries the openings up with the top, so
> the wall *below* each opening grows and the wall above is unchanged. It also
> closed off `side_port`, whose bottom is flush with the case bottom
> (below = 0.000). Openings now stay put.

### Why the openings are modelled the way they are

Each opening is a **horizontal** plan rectangle extruded vertically, not a
rectangle drawn on the wall. A wall sketch puts the opening's height into
sketch geometry, and sketch points are dumb coordinates — they cannot follow a
parameter without driven dimensions. Extruding vertically instead moves the
height into the extrude's `startExtent` offset and depth, both real feature
parameters that accept expressions. That is what makes the height above the
case bottom an explicit, inspectable number.

### Checking it outside Fusion

`verify_rebuild.py` mirrors the same parameter:

```
EXTRA_DEPTH=3 /Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd verify_rebuild.py
```

```
EXTRA_DEPTH   volume        bbox Y            usb_port below/above
0             19261.1 mm3   -12.96 .. 3.53    2.740 / 2.294
3             21062.7 mm3   -12.96 .. 6.53    2.740 / 5.294
```

Top rises by exactly 3 mm, bottom unmoved, still a valid solid, and the growth
is entirely above the opening.

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
