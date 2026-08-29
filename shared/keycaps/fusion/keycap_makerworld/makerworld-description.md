# Parametric Choc Keycap

This is a native Fusion model for Kailh Choc v1 switches, built for people who
want to tune the feel of a low-profile key instead of stretching an STL. The
twin-stem interface and 17.5 × 16.5 mm footprint stay fixed. Eleven dimensions
that affect height, dish, sweep, wall thickness, and edge feel remain
adjustable.

The complete Choc stems are fixed at 3.1 mm, with 1.4 mm extending below the
skirt. Taller settings add solid keycap thickness above a fixed internal
ceiling instead of growing two long posts up to the fingertip surface. That
reduces leverage on the stems during installation and removal, and keeps the
switch seating geometry consistent between short and tall permutations.

## Why 100% infill

A keycap is so small that sparse infill saves very little time or material.
The upper keycap body is solid geometry, and using 100% infill keeps every
remaining enclosed printable region dense. This reduces flex, reinforces the
stem mount, and gives each variation a more consistent sound and feel. It also
removes an unnecessary variable when comparing parameter changes. The fixed
lower cavity remains open for the switch; infill does not close that space.

Solid infill cannot rescue weak layer adhesion. Keep the supplied side-edge
orientation, normal supports, and brim.

## Why PLA Matte

Bambu PLA Matte gives the fingertip surface a dry, low-glare finish that hides
minor layer and support marks better than a glossy filament. Paired with a
0.2 mm nozzle, it preserves the shallow dish and small chamfers without making
the cap look overly shiny. Matte PLA is not unusually tough, which is another
reason to keep the small enclosed regions solid and to test one stem fit before
printing a set.

## Recommended print recipe

| Setting | Value |
| --- | --- |
| Printer | Bambu Lab A1 mini |
| Nozzle | 0.2 mm |
| Filament | Bambu PLA Matte |
| Layer height | 0.08 mm |
| Walls | 3 |
| Infill | 100% |
| Supports | Normal (auto) |
| Brim | 3 mm outer brim |
| Orientation | Standing on a long side edge |
| Plate | Clean Textured PEI Plate |

## Print one cap or a full set

Open the 3MF for the shape you want. Select the keycap on the plate or in the
Objects list, then use **Copy** and **Paste** (`Cmd+C` / `Cmd+V` on macOS,
`Ctrl+C` / `Ctrl+V` on Windows) until the plate contains the quantity you need.
Run **Arrange All**, confirm that every copy is still standing on its side and
inside the build area, then slice again. Copies retain the source object's
orientation and settings.

For a mixed set, open the required configurations and copy the desired caps
into one project before arranging and slicing.

## Adjustable dimensions

| Parameter | Range |
| --- | --- |
| Skirt height | 1.2–2.4 mm |
| Tapered body height | 1.5–3.0 mm |
| Fingertip diameter | 11.0–13.4 mm |
| Raised top height | 0.8–2.5 mm |
| Dish depth | 0.3–1.2 mm |
| Top sweep | -10° to +10° |
| Wall thickness | 0.9–1.5 mm |
| Upper body chamfer | 0.15–0.45 mm |
| Bottom perimeter chamfer | 0.15–0.45 mm |
| Fingertip rim chamfer | 0.15–0.45 mm |
| Skirt transition chamfer | 0.15–0.45 mm |

If dish depth is greater than the requested raised-top height, the model uses
the dish depth as the effective raised height. That keeps the dish open to the
top surface instead of trapping a thin internal void inside the solid body.

Top sweep angles the complete upper surface—including the upper loft, raised
rim, and concave dish—while the skirt and stem interface stay fixed. Leave it
at `0°` for the original level cap; change the sign to reverse the direction.
Start around `4°–6°` for a subtle row-to-row change before trying the ends of
the range.

## Plate preparation

The side-edge contact patch is narrow, so a clean plate matters. Wash it with
warm water and plain dish soap, dry it with a clean lint-free towel, and handle
it by the edges afterward. Re-clean the plate before a batch rather than after
the first cap releases.

## Before committing to a set

Print one cap, let it cool, remove the brim and normal supports carefully, and
check both stems. Choc stem fit changes with printer calibration, material,
cooling, and line width.

The gallery compares representative parameter combinations. The smooth images
are renderings, not photographs of finished prints. The flat-face designs are
companion experiments from the same Fusion generator; the current MakerWorld
customizer uses the raised circular fingertip surface.
