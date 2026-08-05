# mesh_to_brep

Fusion script: mesh file → **editable B-Rep solid**.

## Why not the STEP files in the parent folder

`../stl_to_step.py` (FreeCAD) wraps every mesh triangle in its own planar
B-Rep face. `typeractive_case-bottom-3dp-meshopt.step` has 2078 faces for a
2078-triangle STL. It's a valid solid, but you cannot push/pull a face or
add a fillet — each "flat" wall is hundreds of coplanar triangles, and
OpenCascade's `removeSplitter()` only merges 2078 → 1800 because mesh
vertices carry float noise.

Fusion's Prismatic mesh conversion instead clusters facets into face groups
and fits **real analytic surfaces**. The Typeractive bottom case has 19
cylindrical regions (screw bosses, corner radii) that come back as true
cylinders rather than polygon strips.

## Run

1. Fusion → `Utilities` → `Add-Ins` → `Scripts and Add-Ins` (`Shift + S`).
2. `My Scripts` → `mesh_to_brep` → `Run`.

Already symlinked into
`~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/Scripts/`,
so edits here take effect on the next run. If it isn't listed, add it with
`+` and select this folder.

A new design opens with one solid body. A dialog reports facet / face /
edge counts and volume.

## Tune

Edit `PARAMS` at the top of `mesh_to_brep.py`.

| Param | Default | Meaning |
|---|---|---|
| `stl_path` | Typeractive bottom case | Source mesh. Empty string → file picker |
| `units` | `mm` | Units the mesh is authored in |
| `method` | `prismatic` | `prismatic` (CAD parts) / `faceted` / `organic` (scans) |
| `generate_face_groups` | `True` | Partition mesh before converting — prismatic needs this |
| `face_group_method` | `accurate` | `accurate` (surface fit) or `fast` (normal angle) |
| `boundary_tolerance_mm` | `0.1` | accurate: max facet deviation. Raise to merge harder |
| `angle_threshold_deg` | `20` | fast only |
| `min_face_group_size` | `10` | fast only |
| `organic_accuracy` | `high` | organic only |
| `parametric` | `True` | Keep conversion in the timeline vs. one-shot base feature |

## If conversion fails or over-fragments

- **No solid produced** — raise `boundary_tolerance_mm` (try `0.25`, `0.5`).
- **Too many faces** — same fix; the fitter is splitting one wall into
  several near-coplanar patches.
- **Detail lost** (small chamfers, text) — lower it to `0.05`.
- **Freeform shape** (not this case) — set `method` to `organic`.

Conversion is one-way: the result is a dumb solid, not a feature tree. For a
fully parametric rebuild of this case, see `../corne_choc_travel_case.py`,
which drives geometry from the extracted outlines in
`../typeractive_outline.py` and `../typeractive_inner_bottom.py`.

## Export back out

`File` → `Export` → `STEP` gives a clean B-Rep STEP — the thing the
FreeCAD-generated `.step` files in the parent folder are not.
