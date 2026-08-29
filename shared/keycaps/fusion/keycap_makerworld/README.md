# MakerWorld Parametric Choc Keycap

This project turns the Fusion keycap generator into a MakerWorld Parametric
Model Maker artifact. The product of the project is
`release/MakerWorld_Parametric_Choc_Keycap.f3d`; the Python script is only the repeatable
build/export tool.

## Model contract

- Kailh Choc v1 twin stem
- Choc 18 x 17 mm spacing
- Default footprint: 17.5 x 16.5 mm
- Concave circular top
- Chamfered exterior edges
- Fixed 3.1 mm complete Choc stem height, including 1.4 mm below the skirt
- Fixed 1.7 mm cavity ceiling with a solid upper keycap body
- One solid body in the root component
- Fusion design history enabled
- Opens standing on a long side edge, seated on the XY build plane

Stem type, spacing, top type, edge type, width class, and homing style are
fixed because MakerWorld does not run the Fusion script or its dropdown logic.
Those topology-changing choices belong in separate F3D variants.

The Choc mount does not grow with those height controls. Taller caps add solid
body thickness above the fixed cavity ceiling instead of extending two narrow
posts toward the top surface. This reduces leverage on the stems during
installation and removal while keeping the skirt-to-switch relationship
consistent across permutations.

For raised variants, effective top height is `max(cyl_h; dish_depth)`. This
prevents a dish deeper than its requested pedestal from leaving an enclosed
lens-shaped void inside the otherwise-solid upper body.

The current F3D exposes eleven live MakerWorld controls: skirt height, taper
height, fingertip diameter, fingertip height, dish depth, signed top sweep,
wall thickness, and four independent chamfers (upper perimeter, bottom
perimeter, fingertip rim, and skirt transition). Sweep angles the complete
upper loft, raised fingertip surface, rim, and dish around the cap's left-right
axis while leaving the skirt and switch interface fixed; `0 deg` reproduces the
level design. Every favorite is linked to timeline geometry; there are no
placeholder parameters.

## Build the F3D

1. Keep this folder beside `../keycap_1u_choc`; the build imports that shared
   generator.
2. In Fusion, open **Utilities > Scripts and Add-Ins**.
3. Add this `keycap_makerworld` folder under **My Scripts**.
4. Run `keycap_makerworld`.
5. The script creates a new design, builds one keycap, favorites the public
   parameters, exercises the full local validation matrix, restores the
   defaults, and writes the F3D under `release/`. It also exports the exact STL
   for every validated preset under `release/parameter_variants/` for render
   and geometry comparisons. Three no-pedestal concepts are exported under
   `release/flat_dish_variants/`; their spherical dishes are cut directly into
   the flat upper face. The release F3D and its STL variants are rotated onto
   a side edge as the final timeline operation, so MakerWorld opens them in
   their intended print orientation.

## Bambu Studio projects

The 12 catalog configurations have individual sliced Bambu Studio projects
under `release/print_profiles/`, plus a sampler project containing all 12
configurations on one plate. Rebuild them with:

```sh
python3 print_profiles/build_bambu_3mf_profiles.py
```

The builder flattens Bambu's bundled system presets, slices every existing
edge-oriented catalog STL, and validates the settings and G-code embedded in
each 3MF. Set `BAMBU_STUDIO_BIN` if Bambu Studio is installed somewhere other
than its standard macOS location.

The supplied profile is A1 mini / 0.2 mm nozzle / Bambu PLA Matte, with 0.08
mm layers, three walls, 100% infill, a 3 mm outer brim, normal automatic
supports, and the keycap standing on edge. Each 3MF embeds its matching smooth
gallery render and uses it as the plate thumbnail. Start with a freshly washed build
plate: warm water and plain dish soap, a lint-free dry, and no fingerprints in
the print area. These projects have been archive- and slicer-validated, but
still require a physical test print before publication as MakerWorld print
profiles.

The upper body is solid in the CAD model; 100% slicer infill also keeps every
remaining enclosed printable region dense. Sparse infill is intentionally not
used for any supplied profile.

For the MakerWorld print profile, use
`MakerWorld_Choc_Keycap_12_Config_Sampler_A1mini_0.08mm.3mf`. It contains one
copy of every catalog configuration as 12 separate, edge-oriented objects on
a single A1 mini plate.

The generated Fusion document remains open for inspection. MakerWorld only
receives the saved timeline and will not rerun the script, so repeat the same
boundary checks in MakerWorld before publishing.

## MakerWorld setup

1. Create or edit the MakerWorld model page.
2. Upload `release/MakerWorld_Parametric_Choc_Keycap.f3d` under **Raw Model Files**.
3. Open **Customize** after validation completes.
4. For each displayed input, copy the default, minimum, maximum, and step from
   `makerworld-inputs.json`.
5. Generate the default and boundary combinations listed below.
6. Download the generated 3MF and confirm in Bambu Studio that it remains
   standing on its side edge with a brim and normal supports. Do not lay it
   flat on its underside.
7. To print a set, select the cap in Bambu Studio, copy and paste it until the
   plate has the quantity you need, run **Arrange All**, then reslice. Pasted
   copies retain the source orientation and object settings.

## Required validation

Test these parameter sets both in local Fusion and in MakerWorld:

| Set | Values |
| --- | --- |
| Default | All defaults |
| Minimum | Every parameter at its minimum |
| Maximum | Every parameter at its maximum |
| Thin/tall | Minimum wall and dish; maximum height values |
| Thick/short | Maximum wall and dish; minimum height values |
| Edge stress | All four chamfers at maximum with minimum top height |

For every set, require one body, a clean Fusion recompute, a valid generated
3MF, and no visibly collapsed faces. Before publishing, print stem-fit samples
and at least one complete default keycap.

## Release contents

The release F3D is generated by Fusion and is therefore not present until the
script is run. A public MakerWorld release should contain:

- `MakerWorld_Parametric_Choc_Keycap.f3d`
- A tested 3MF print profile
- The all-in-one 12-configuration sampler from `print_profiles/`
- Twelve edge-oriented Bambu Studio 3MF projects from `print_profiles/`
- Default render and underside/stem photos
- A parameter table copied from `makerworld-inputs.json`
- Material, orientation, support, and stem-fit notes

Prepared render assets are under `media/`:

- `makerworld-realistic-iphone17-workbench-clean-v2.png` — recommended loose-part hero
- `makerworld-realistic-iphone17-installed-clean-v2.png` — recommended installed-use portrait
- `makerworld-realistic-iphone17-hand-detail-clean-v2.png` — recommended scale/detail image
- `parameter-presets-gallery-4x3.png` — six exact Fusion presets at a common camera and scale
- `parameter_presets/parameter-*-cad-4x3.png` — individual clean CAD-style preset renders
- `parameter-permutations-photoreal-catalog.png` — labeled 12-variant catalog with six raised-platform and six flat-face designs
- `catalog_photoreal/*-photoreal-v1.png` — full-resolution realistic black-PLA renders for every catalog variant
- `parameter-permutations-smooth-catalog.png` — revised 12-variant gallery with smooth satin surfaces and no visible print layers
- `parameter-permutations-table.png` — high-resolution comparison table for every catalog parameter
- `catalog_smooth/*-smooth-v2.png` — full-resolution smooth-material renders for every catalog variant
- `catalog_exact/*-exact-prusa-4x3.png` — exact common-camera geometry references derived from the exported Fusion variants and edge-oriented Prusa layer planes
- `makerworld-flat-dish-*-prusa-realistic-4x3.png` — exact flat-dish geometry with sliced layer planes
- `makerworld-flat-dish-*-photoreal-v1.png` — photorealistic enhancements of those exact renders
- `makerworld-cover-4x3-prusa-toolpaths.png` — exact external-perimeter toolpath reference
- `makerworld-cover-4x3-prusa-surface.png` — shaded reference using the sliced layer planes
- Earlier realistic, stylized, and smooth renders remain available for comparison.

The realistic images are AI composites constrained by the PrusaSlicer-derived
geometry; they are not documentary print photos. Add real stem-fit and
finished-print photos before publishing when possible.

The corresponding 12 exported STLs and their parameter values are under
`release/catalog_permutations/`, with the machine-readable index in
`catalog-permutations.json`.

The corresponding sliced projects and their hashes, estimated times, object
counts, and parameter values are under `release/print_profiles/`, indexed by
`bambu-3mf-profiles.json`.

Later variants should be separate MakerWorld-compatible F3Ds: wide Choc,
MX stem, convex top, filleted edge, and homing-feature editions.
