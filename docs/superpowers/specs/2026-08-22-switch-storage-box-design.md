# Parametric Switch Storage Box — Design

**Date:** 2026-08-22
**Status:** Approved design, pending implementation plan
**Target:** MakerWorld Parametric Model Maker

## Purpose

A 3D-printable box that stores loose mechanical keyboard switches in individual
snap-fit slots. Switches are held firmly enough not to fall out when the box is
tipped or carried, but loose enough to remove with fingers — no switch puller.

Boxes stack. Each box takes a front label and an optional lid sticker.

## Model contract

- Switches sit pins-down in individual pockets, stems facing up
- Two opposing ribs per pocket provide the snap
- Rows and columns are live MakerWorld parameters
- Minimum wall thickness 1.75 mm
- 10 mm fillets on vertical corners, valid across the whole size range
- 75° draft on the stackable ring around the base
- Front label is a flush recessed pocket for a paper, printed, or vinyl label
- Lid sticker recess is 0.4 mm (two layers at 0.2 mm)
- Fusion design history enabled, single body per exported file

## Switch dimensions

All figures below are read from official manufacturer drawings. Sources are
listed at the end of this document.

| Dimension | Cherry MX | Choc v1 (PG1350) | Choc v2 (PG1353) |
| --- | --- | --- | --- |
| Top flange (X × Y) | 15.60 × 15.60 | 15.00 × 15.00 | 15.00 × 15.00 |
| Bottom housing (X × Y) | ~13.90 (see note) | 13.80 × 13.80 | 13.95 ± 0.05 |
| Body height, no stem | 11.60 | 5.70 | 5.70 |
| Housing below flange | 5.00 | 2.20 | 2.20 |
| Total height with stem | 15.20 | ~8.00 | ~8.00 |
| Pin protrusion below housing | 3.30 | 3.00 | 3.30 |
| Centre post diameter | 3.99 ± 0.10 | 3.40 | 5.30 |
| Plate cutout | 13.995 ± 0.05 | 13.80 | 13.95 ± 0.05 |
| Bottom wall geometry | Tapered inward | Straight | Straight |

### Cherry MX bottom housing note

Cherry does not dimension the bottom housing in any published drawing. The
plate cutout is specified as 13.995 mm, so the housing must pass through it;
the widest point sits just under the flange at approximately 13.90 mm. This
figure is derived, not published, and is the one dimension in this design that
requires a physical test print to confirm.

The MX skirt is drafted, narrowing toward the pins. The pocket ribs therefore
grip high on the skirt, immediately below the flange, where the section is
widest and most consistent.

## Variant strategy

MakerWorld's customizer reads numeric parameters from a saved Fusion timeline.
It cannot execute a script, evaluate a dropdown, or suppress a body. Any choice
that changes topology must ship as a separate F3D.

Choc v1 and Choc v2 differ by 0.15 mm across the bottom housing. That is
smaller than the dimensional spread of a typical FDM print, so one pocket
profile serves both; the rib depth parameter absorbs the difference. Body
height is identical at 5.70 mm.

Cherry MX is twice as tall and tapered, so it needs its own pocket and its own
overall box height.

Two geometry families, each in a lidless and a lidded edition:

| File | Pocket | Lid |
| --- | --- | --- |
| `switchbox_choc.f3d` | 13.90 sq, straight | no |
| `switchbox_choc_lidded.f3d` | 13.90 sq, straight | yes |
| `switchbox_mx.f3d` | 13.95 sq, drafted | no |
| `switchbox_mx_lidded.f3d` | 13.95 sq, drafted | yes |

The Choc pocket is nominally 13.90 mm — centred between v1's 13.80 and v2's
13.95 — with ribs sized to grip either.

## Geometry

### Pocket

Each pocket is a square hole with a recessed floor. The floor sits below the
pocket mouth by the switch's below-flange housing depth, so the flange rests on
the box's top face and forms a positive depth stop. A central pin relief
recess, sized to clear the widest centre post plus both contact pins, is cut
into the floor so nothing bottoms out.

Pin relief depth is 3.60 mm for both families: the largest pin protrusion is
3.30 mm, plus 0.30 mm clearance.

| Parameter | Choc | MX |
| --- | --- | --- |
| Pocket X/Y | 13.90 | 13.95 |
| Pocket depth to floor | 2.60 | 5.40 |
| Pin relief diameter | 7.00 | 8.00 |
| Pin relief depth | 3.60 | 3.60 |
| Floor thickness below relief | 1.75 | 1.75 |

Pocket depth is the below-flange housing depth plus 0.40 mm clearance.

### Snap ribs

Two ribs sit on opposing pocket walls, on the X axis, centred in Y. Each rib is
a shallow half-round running vertically down the wall, stopping short of the
floor so the switch self-centres on entry.

| Parameter | Value | Note |
| --- | --- | --- |
| `rib_depth` | 0.20 | Protrusion into the pocket, per side |
| Rib width | 2.00 | Along the wall |
| Rib height | 1.60 | Vertical run |
| Rib top offset | 0.40 | Below pocket mouth |

Total interference is 0.40 mm across the diagonal, split over two ribs. That is
a light elastic squeeze in PLA at these wall thicknesses — enough to resist
gravity and shaking, not enough to need a tool.

`rib_depth` is the primary tuning parameter and is exposed to MakerWorld. Lower
it toward 0.15 if switches bind; raise it toward 0.28 if they fall out.

### Walls, fillets, and the fillet clamp

Outer walls are `wall` thick, minimum 1.75 mm, default 2.00 mm. Interior
dividers between pockets are `wall` thick as well, which sets pocket pitch:

```
pitch = pocket_size + wall
```

For Choc at default wall this is 15.90 mm; for MX, 15.95 mm.

Overall box footprint:

```
box_x = cols * pitch + wall
box_y = rows * pitch + wall
```

Vertical corner fillets default to 10 mm. A 10 mm fillet on each of two corners
consumes 20 mm of an edge, so a sufficiently narrow box could not accept it —
Fusion raises a hard timeline error rather than clamping, which in a MakerWorld
model means a failed generation for the customer.

The minimum supported box is 2 × 2. At that size the footprint is 33.05 mm even
at minimum wall thickness, which leaves 13.05 mm of flat run between two 10 mm
fillets. The full fillet range is therefore safe everywhere in the supported
parameter space, and `corner_fillet` needs no clamp — its published maximum is
a flat 10 mm.

A guard remains in the generator as a build-time assertion rather than a
runtime clamp:

```
assert (min(box_x, box_y) - 2 * corner_fillet) >= 4.0
```

This fires during the validation matrix if a future change to pocket size, wall
range, or the row and column minimums ever shrinks the smallest box below the
safe threshold. It protects the invariant without adding a parameter dependency
that MakerWorld cannot express.

Single-row and single-column boxes are not supported. At one column the
footprint is under 20 mm, no meaningful fillet fits, and the stack ring has no
room to inset. Minimum is 2 × 2.

### Stacking

The base carries a ring that steps down from the outer wall, drafted at 75°
measured from horizontal. The lid top carries a matching recess. A box without
a lid receives the next box's ring in its open top instead, so both lidded and
lidless boxes stack.

| Parameter | Value |
| --- | --- |
| `stack_angle` | 75° |
| Ring height | 2.50 |
| Ring inset from outer wall | 1.20 |
| Stack clearance, per side | 0.25 |

The draft means the ring self-centres as it drops in and does not bind.

### Lid

The lid is a flat plate with a perimeter skirt that snaps over the box's outer
wall. A shallow bead on the inner skirt face engages a matching groove on the
box's outer wall.

| Parameter | Value |
| --- | --- |
| `lid_gap` | 0.20 |
| Skirt height | 4.00 |
| Bead depth | 0.30 |
| Bead position below lid underside | 2.50 |

Bead depth is deliberately larger than `rib_depth`: the lid skirt flexes along
its whole perimeter and needs more interference to feel positive.

### Labels

**Front label pocket.** A rectangle recessed into the front wall, centred on
the flat run between the corner fillets. Depth 0.40 mm. The generator thickens
the front wall locally to 2.15 mm under the pocket so at least 1.75 mm of
material remains behind it at any wall setting.

The label clamp is the one that genuinely binds. Available flat run is:

```
flat_run = box_x - 2 * corner_fillet
label_w_max = flat_run - 2.0
```

At the smallest box, 2 × 2 at minimum wall, the flat run is 13.05 mm and
`label_w_max` is 11.05 mm — well under the 30 mm default. The generator clamps
`label_w` to this value and publishes the clamped maximum per variant. A 2 × 2
box gets a small label; a 4 × 4 box gets the full 30 mm.

**Lid sticker recess.** A rectangle recessed 0.40 mm into the lid top — two
layers at 0.20 mm. Default 35 × 35 mm, clamped to the lid footprint less the
fillet radius.

Both recesses have a 0.25 mm chamfer at the mouth so a sticker seats without
catching.

## MakerWorld parameters

Every parameter below drives live timeline geometry. There are no placeholders.

| Parameter | Default | Min | Max | Step |
| --- | --- | --- | --- | --- |
| `rows` | 4 | 2 | 10 | 1 |
| `cols` | 4 | 2 | 10 | 1 |
| `wall` | 2.00 | 1.75 | 3.50 | 0.05 |
| `rib_depth` | 0.20 | 0.10 | 0.35 | 0.01 |
| `corner_fillet` | 10.00 | 2.00 | 10.00 | 0.50 |
| `label_w` | 30.00 | 8.00 | clamped | 1.00 |
| `label_h` | 12.00 | 6.00 | 25.00 | 1.00 |
| `label_depth` | 0.40 | 0.20 | 1.00 | 0.10 |
| `sticker_w` | 35.00 | 8.00 | clamped | 1.00 |
| `sticker_h` | 35.00 | 8.00 | clamped | 1.00 |
| `sticker_recess` | 0.40 | 0.20 | 0.80 | 0.10 |
| `stack_angle` | 75.00 | 70.00 | 85.00 | 1.00 |
| `lid_gap` | 0.20 | 0.10 | 0.40 | 0.05 |

Clamped maxima are computed per variant at build time and written into
`makerworld-inputs.json` alongside the F3D.

Switch type, lid presence, row/column pitch, and pocket profile are fixed per
file. They change topology and cannot be customizer inputs.

## Resulting box sizes

Default 4 × 4, wall 2.00:

| | Choc | MX |
| --- | --- | --- |
| Footprint | 65.6 × 65.6 | 65.8 × 65.8 |
| Height, lidless | 10.45 | 13.25 |
| Height, with lid | 13.95 | 16.75 |
| Switches held | 16 | 16 |

Box height is pocket depth plus pin relief depth plus floor thickness plus the
stack ring. The Choc box is 2.8 mm shorter because its housing sits 2.80 mm
less deep below the flange.

## Implementation

A shared Python generator, `switchbox/switchbox.py`, follows the structure of
`keycaps/fusion/keycap_makerworld/keycap_makerworld.py`: build the design in a
new document, favourite the public parameters, run the validation matrix,
restore defaults, and export.

Per-variant configuration lives in a dictionary keyed by variant name, holding
pocket size, pocket depth, pin relief dimensions, draft flag, and lid flag. One
script run produces all four F3Ds plus their input contracts.

Layout:

```
switchbox/
  switchbox.py
  switchbox.manifest
  makerworld-inputs.json
  README.md
  release/
    switchbox_choc.f3d
    switchbox_choc_lidded.f3d
    switchbox_mx.f3d
    switchbox_mx_lidded.f3d
```

## Validation

Run each set in local Fusion and again in MakerWorld before publishing.

| Set | Values |
| --- | --- |
| Default | All defaults |
| Minimum | Every parameter at its minimum |
| Maximum | Every parameter at its maximum |
| Smallest box | 2 × 2, maximum wall, maximum fillet |
| Largest box | 10 × 10, minimum wall, default fillet |
| Fillet stress | Maximum fillet at minimum rows, columns, and wall |
| Label stress | Maximum label and sticker on a 2 × 2 box |
| Thin wall | Minimum wall with maximum rib depth and label depth |

Each set must produce one body, a clean recompute, a valid generated 3MF, and
no collapsed faces. The label set exists specifically to prove the clamp holds; an unclamped
label on a small box is the failure mode most likely to reach a customer. The
fillet set proves the build-time assertion is satisfied at the smallest box.

Physical validation before publishing:

- Print a 2 × 2 test box in each family
- Confirm switches snap in and pull out by hand
- Confirm two boxes stack and separate cleanly
- Confirm the lid snaps on and comes off without tools
- Confirm the MX bottom housing figure of 13.90 mm, the one derived dimension

## Print orientation

Boxes print open side up on the build plate, no supports. The pin relief
recesses are shallow and self-supporting. The stack ring's 75° draft is within
the unsupported overhang limit.

Lids print top face down so the sticker recess forms against the plate and
comes out smooth.

## Sources

- Kailh PG1350 (Choc v1), drawing CPG135001D01, dated 2017-03-31 —
  <https://cdn-shop.adafruit.com/product-files/5113/CHOC+keyswitch_Kailh-CPG135001D01_C400229.pdf>
- Kailh PG1353 (Choc v2), drawing CPG1353D01D01-16, dated 2024-05-08 —
  <https://raw.githubusercontent.com/keyboardio/keyswitch_documentation/master/datasheets/Kailh/CPG1353D01D01-16.pdf>
- Cherry MX Series desktop profile catalogue drawings —
  <https://datasheet.octopart.com/MX1A-11NW-Cherry-datasheet-34676.pdf> and
  <https://cdn.sparkfun.com/datasheets/Components/Switches/MX%20Series.pdf>

Every dimension in the switch table is read from these drawings, except the
Cherry MX bottom housing footprint and skirt draft angle, which Cherry does not
publish. Both are flagged in the validation list for physical confirmation.
