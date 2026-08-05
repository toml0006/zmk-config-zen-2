"""
Independently rebuild the case from typeractive_bottom_profile.py using
FreeCAD, and check it against the source mesh. Run this after editing the
profile data or CUTOUTS to confirm the geometry still closes.

    /Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd verify_rebuild.py

Writes corne_bottom_case.step next to this file. That STEP is a genuine
analytic B-Rep, so it imports into Fusion with no subscription needed --
useful if you want the body without running the Fusion script.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import Part
from FreeCAD import Vector

import typeractive_bottom_profile as P

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'corne_bottom_case.step')

# Mirrors the case_extra_height user parameter in the Fusion script. The case
# grows upward from a fixed bottom: the wall band below the openings gets
# taller, and the openings, plate and screw holes all rise by the same amount.
# Leave at 0.0 to compare against the source mesh. Override without editing:
#   EXTRA_HEIGHT=3 freecadcmd verify_rebuild.py
EXTRA = float(os.environ.get('EXTRA_HEIGHT', '0'))

# Mirrors PORT_FRAMES / PORT_FRAME_* in the Fusion script. The fillet at the
# floor-to-wall junction is NOT modelled here -- selecting that edge loop is
# fiddly in FreeCAD and it does not change the checks this script makes.
FRAMES = os.environ.get('PORT_FRAMES', '1') != '0'
FRAME_T = 1.2
FRAME_MARGIN = 2.0
MESH_VOLUME = 19187.7          # measured on case-bottom-3dp-meshopt.stl
MESH_BBOX = 'X -134.99..-2.09  Y -12.97..3.53  Z -37.19..51.00'


def face_at(points, y):
    vs = [Vector(x, y, z) for x, z in points]
    return Part.Face(Part.makePolygon(vs + [vs[0]]))


def build():
    L, T = P.LEVELS, P.WALL_THICKNESS
    # Mesh frame here (+Y up, floor plate on top); the Fusion script works in
    # the corrected frame where the floor sits at z = 0. Same geometry.
    #
    # Only the RIB grows. The floor, the main perimeter wall and its rim are
    # fixed; the rib extends away from the rim by EXTRA, and both openings --
    # which lie inside the rib's footprint -- travel with it. In mesh
    # coordinates "up" is -EXTRA.
    skirt_bottom = L['skirt_bottom']
    rib_bottom = L['rib_bottom'] - EXTRA

    plate = face_at(P.PLATE_OUTLINE, L['plate_bottom']).extrude(
        Vector(0, L['plate_top'] - L['plate_bottom'], 0))

    outer = face_at(P.PLATE_OUTLINE, skirt_bottom)
    inner = Part.Face(outer.OuterWire.makeOffset2D(-T, 0, False, False))
    skirt = outer.cut(inner).extrude(
        Vector(0, L['plate_bottom'] - skirt_bottom, 0))

    rib = face_at(P.RIB_OUTLINE, rib_bottom).extrude(
        Vector(0, skirt_bottom - rib_bottom, 0))

    shape = plate.fuse(skirt).fuse(rib).removeSplitter()

    for x, z, r in P.SCREW_HOLES:
        shape = shape.cut(Part.makeCylinder(
            r, 20, Vector(x, L['plate_bottom'] - 5, z), Vector(0, 1, 0)))

    # Reinforcing collars around the openings, added before the holes are cut.
    if FRAMES:
        for c in P.CUTOUTS:
            w = c['width'] / 2.0 + FRAME_MARGIN
            h = c['height'] + 2 * FRAME_MARGIN
            y0 = c['y'] - EXTRA - c['height'] / 2 - FRAME_MARGIN
            n = -1.0 if c['wall'] in ('+X', '+Z') else 1.0
            a1, a2 = c['at'] + n * T, c['at'] + n * (T + FRAME_T)
            lo, hi = min(a1, a2), max(a1, a2)
            if c['wall'] in ('+X', '-X'):
                box = Part.makeBox(hi - lo, h, 2 * w,
                                   Vector(lo, y0, c['along'] - w))
            else:
                box = Part.makeBox(2 * w, h, hi - lo,
                                   Vector(c['along'] - w, y0, lo))
            shape = shape.fuse(box)
        shape = shape.removeSplitter()

    for c in P.CUTOUTS:
        w, h, d = c['width'], c['height'], T * 6
        y0 = c['y'] - EXTRA - h / 2
        if c['wall'] in ('+X', '-X'):
            box = Part.makeBox(d, h, w, Vector(
                c['at'] - d / 2, y0, c['along'] - w / 2))
        else:
            box = Part.makeBox(w, h, d, Vector(
                c['along'] - w / 2, y0, c['at'] - d / 2))
        shape = shape.cut(box)
        print('  cut %-10s mesh y %8.3f ..%8.3f   (rib end %8.3f, '
              'gap to rib end %.3f)'
              % (c['name'], y0, y0 + h, rib_bottom, y0 - rib_bottom))

    return shape.removeSplitter()


shape = build()
bb = shape.BoundBox
if EXTRA:
    print('EXTRA_HEIGHT = %.3f mm (mesh comparison below is expected to '
          'differ by roughly band_area * EXTRA)' % EXTRA)
delta = shape.Volume - MESH_VOLUME
print('\nrebuild : vol %.1f mm3  faces %d  edges %d  valid %s'
      % (shape.Volume, len(shape.Faces), len(shape.Edges), shape.isValid()))
print('mesh    : vol %.1f mm3  ->  delta %+.1f mm3 (%+.2f%%)'
      % (MESH_VOLUME, delta, 100.0 * delta / MESH_VOLUME))
print('bbox    : X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f'
      % (bb.XMin, bb.XMax, bb.YMin, bb.YMax, bb.ZMin, bb.ZMax))
print('mesh    : %s' % MESH_BBOX)
shape.exportStep(OUT)
print('wrote %s' % OUT)
