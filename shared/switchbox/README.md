# Parametric Switch Storage Box

A MakerWorld-ready parametric box that stores loose keyboard switches in
individual snap-fit pockets. Built in Fusion; MakerWorld regenerates it live
from the favorited parameters.

Design document: `../docs/superpowers/specs/2026-08-22-switch-storage-box-design.md`

## Current release

`release/switchbox_choc.f3d` — fits Kailh Choc v1 (PG1350) and Choc v2
(PG1353). Their bottom housings differ by 0.15 mm, which is inside FDM
tolerance, so one pocket profile serves both.

`release/switchbox_choc_4x4.stl` — the default 4 x 4 configuration, for a
quick test print without going through MakerWorld.

## What the customer controls

Nine parameters are exposed. Every one drives live timeline geometry.

| Parameter | Default | Range | Effect |
| --- | --- | --- | --- |
| `cols` | 4 | 2–10 | Switch columns |
| `rows` | 4 | 2–10 | Switch rows |
| `wall` | 2.0 | 1.75–3.5 | Wall and divider thickness |
| `rib_depth` | 0.2 | 0.1–0.35 | Snap tightness per side |
| `corner_fillet` | 10 | 2–10 | Vertical corner radius |
| `label_w` | 30 | 8–60 | Front label recess width |
| `label_h` | 12 | 6–25 | Front label recess height |
| `label_depth` | 0.4 | 0.2–1.0 | Front label recess depth |
| `stack_angle` | 75 | 70–85 | Stacking ring draft |

Exact minimums, maximums, and steps are in `makerworld-inputs.json`.

## Two things worth knowing before editing this model

**Counts must carry units.** MakerWorld drops dimensionless parameters from the
customizer even when they are favorited. `cols` and `rows` are therefore
declared in millimetres and divided by `1 mm` wherever they are used as counts,
so the units cancel and the arithmetic stays correct. Removing the unit would
silently remove the two most important sliders from the published model.

**Label dimensions are clamped inside the model.** `label_w`, `label_h`, and
`label_depth` each feed a `min()` expression rather than driving geometry
directly:

```
label_w_eff = min(label_w; box_x - 2*corner_fillet - 2 mm)
label_h_eff = min(label_h; box_h - ring_h - 2 mm)
label_d_eff = max(0.2 mm; min(label_depth; min(0.6 mm; wall - 1.2 mm)))
```

Without these, a large label on a small box cuts through the corner fillets,
runs into the stacking ring, or leaves too little wall behind it. The clamps
mean an out-of-range value produces a smaller label instead of a failed
generation.

The depth clamp reserves 1.2 mm rather than the 1.75 mm used for structural
walls. Reserving the full 1.75 mm leaves exactly zero depth when `wall` is at
its 1.75 mm minimum, and a zero-depth cut fails outright. A shallow cosmetic
recess does not need the same reserve as a load-bearing wall; 1.2 mm still
prints as a solid multi-perimeter face.

## Validation

Eight configurations were run in Fusion. Each is checked for a single body, no
unhealthy timeline features, correct outer dimensions, a label that clears the
stacking ring and stays under the top face, and adequate material behind the
label recess.

| Case | Footprint | Label depth | Wall behind | Result |
| --- | --- | --- | --- | --- |
| Default 4 x 4 | 65.6 x 65.6 | 0.40 | 1.60 | Pass |
| All minimum | 33.0 x 33.1 | 0.20 | 1.55 | Pass |
| All maximum | 177.5 x 177.5 | 0.60 | 2.90 | Pass |
| Smallest box | 38.3 x 38.3 | 0.60 | 2.90 | Pass |
| Thin wall | 95.6 x 64.4 | 0.55 | 1.20 | Pass |
| Wide and short | 161.0 x 33.8 | 0.40 | 1.60 | Pass |
| Tall and narrow | 33.8 x 161.0 | 0.30 | 1.70 | Pass |
| Min wall, max label | 64.4 x 64.4 | 0.55 | 1.20 | Pass |

Height is 10.45 mm in every configuration; only the footprint changes.

Still to do before publishing: repeat these six in the MakerWorld customizer
itself, confirm all nine sliders appear, and print a 2 x 2 test box to check
the snap fit against real switches.

## Not yet built

- The MX variant. Cherry MX is 11.6 mm tall against Choc's 5.70 mm and its
  skirt is drafted, so it needs its own pocket geometry and box height.
- The lid. MakerWorld cannot toggle a body on or off from a parameter, so
  lidded editions ship as separate files.

## Print notes

Print open side up, no supports. The pin relief recesses are shallow and
self-supporting, and the stacking ring's 75 degree draft is within the
unsupported overhang limit.
