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

## Raising the case: `case_extra_height`

The script creates one Fusion **user parameter**, `case_extra_height`,
default `0 mm`. After the first run it lives in `Modify` → `Change
Parameters`, so you can change it there and the model rebuilds — no need to
re-run the script.

It grows the case **upward from a fixed bottom**. The wall band below the
sidewall openings gets taller, and the openings, the plate and the screw
holes all rise by the same amount. The case bottom, the shelled underside
and the rib stay exactly where they are.

Measured at `case_extra_height = 3 mm`:

| | 0 mm | 3 mm |
|---|---|---|
| `usb_port` (Y) | −4.160…−0.260 | −1.160…2.740 |
| `side_port` (Y) | −6.900…−3.400 | −3.900…−0.400 |
| bbox Y | −12.96…3.53 | −12.96…**6.53** |
| volume | 19261.1 mm³ | 21062.7 mm³ |

Bottom fixed, top +3, both openings +3. The volume rises by the skirt band
area (~600.5 mm²) times the parameter.

`side_port`'s underside sits flush with the case bottom at 0 mm, so raising
the parameter is what creates a wall band beneath it — the edge count drops
from 559 to 555 as its lower edge stops coinciding with the case bottom.

### How it is wired

Sketch geometry cannot be driven by an expression without adding driven
dimensions, so the openings are **not** sketched on the wall face. Each one
is sketched as a plan-view footprint on the case bottom and cut upward, with
its vertical position in the extrude's `startExtent` and its height in the
extrude depth. Those are real feature parameters, so both can reference
`case_extra_height`.

The same applies to the main extrusion height, the plate-top sketch plane and
the screw-hole cut depth — the last two must track the top, or the holes miss
the plate.

To check a value without opening Fusion:

```
EXTRA_HEIGHT=3 /Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd verify_rebuild.py
```

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
