"""
Move rectangular cutouts in a STEP file up by a given Y amount.

Usage:
  /Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd shift_cutouts.py

Edit the CUTOUTS list below with your hole positions (XYZ ranges of each
cutout's BBox in the STL/STEP coordinate frame). The script fuses a box
at the original location (fills the old hole) then cuts an identical box
shifted up in Y (makes a new hole at the new height).

Coords are in mm, in the STEP file's native frame:
  X = wide axis (case length)
  Y = vertical (case thickness, up = +Y)
  Z = depth (case front-back)
"""

import Part
import sys

# --------------------------------------------------------------------------
SOURCE   = '/Users/jackson/dev/keyboards/cases/corne-choc-travel/typeractive_case-bottom-3dp-meshopt.step'
OUTPUT   = '/Users/jackson/dev/keyboards/cases/corne-choc-travel/typeractive_case-bottom-3dp-meshopt_shifted.step'
DY_SHIFT = 2.33    # mm, positive = up

# Each cutout: (x_min, x_max, y_min, y_max, z_min, z_max).
# Make X span the wall thickness (outer face minus a few mm inward).
# Y is the cutout's vertical extent at the OLD position.
# Z is the cutout's depth extent at the OLD position.
#
# The known +X-wall cutout on case-bottom-3dp:
CUTOUTS = [
    # +X wall hole: 19mm wide (Z) x 7mm tall (Y), outer at X=-2.09
    (-5.5, -2.0, -5.71, 1.29, -7.65, 11.35),
    # SECOND CUTOUT: replace these numbers with the real coords.
    # If on the same +X wall, only Y and Z change between holes; X stays the same.
    # (-5.5, -2.0,  y_min,  y_max,  z_min,  z_max),
]
# --------------------------------------------------------------------------


def main():
    shape = Part.Shape()
    shape.read(SOURCE)
    sys.stderr.write(f'Loaded: faces={len(shape.Faces)} vol={shape.Volume:.0f}\n')

    for (x0, x1, y0, y1, z0, z1) in CUTOUTS:
        w = x1 - x0
        h = y1 - y0
        d = z1 - z0
        fill = Part.makeBox(w, h, d).translate((x0, y0, z0))
        cut  = Part.makeBox(w, h, d).translate((x0, y0 + DY_SHIFT, z0))
        sys.stderr.write(f'  fusing fill {w:.1f}x{h:.1f}x{d:.1f} at ({x0:.1f},{y0:.1f},{z0:.1f})\n')
        shape = shape.fuse(fill)
        sys.stderr.write(f'  cutting new at Y={y0+DY_SHIFT:.2f}\n')
        shape = shape.cut(cut)

    shape.exportStep(OUTPUT)
    sys.stderr.write(f'Wrote: {OUTPUT}  faces={len(shape.Faces)} vol={shape.Volume:.0f}\n')


main()
