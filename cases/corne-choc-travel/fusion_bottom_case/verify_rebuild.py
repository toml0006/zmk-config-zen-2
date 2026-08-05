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
MESH_VOLUME = 19187.7          # measured on case-bottom-3dp-meshopt.stl
MESH_BBOX = 'X -134.99..-2.09  Y -12.97..3.53  Z -37.19..51.00'


def face_at(points, y):
    vs = [Vector(x, y, z) for x, z in points]
    return Part.Face(Part.makePolygon(vs + [vs[0]]))


def build():
    L, T = P.LEVELS, P.WALL_THICKNESS

    plate = face_at(P.PLATE_OUTLINE, L['plate_bottom']).extrude(
        Vector(0, L['plate_top'] - L['plate_bottom'], 0))

    outer = face_at(P.PLATE_OUTLINE, L['skirt_bottom'])
    inner = Part.Face(outer.OuterWire.makeOffset2D(-T, 0, False, False))
    skirt = outer.cut(inner).extrude(
        Vector(0, L['plate_bottom'] - L['skirt_bottom'], 0))

    rib = face_at(P.RIB_OUTLINE, L['rib_bottom']).extrude(
        Vector(0, L['skirt_bottom'] - L['rib_bottom'], 0))

    shape = plate.fuse(skirt).fuse(rib).removeSplitter()

    for x, z, r in P.SCREW_HOLES:
        shape = shape.cut(Part.makeCylinder(
            r, 20, Vector(x, L['plate_bottom'] - 5, z), Vector(0, 1, 0)))

    for c in P.CUTOUTS:
        w, h, d = c['width'], c['height'], T * 6
        if c['wall'] in ('+X', '-X'):
            box = Part.makeBox(d, h, w, Vector(
                c['at'] - d / 2, c['y'] - h / 2, c['along'] - w / 2))
        else:
            box = Part.makeBox(w, h, d, Vector(
                c['along'] - w / 2, c['y'] - h / 2, c['at'] - d / 2))
        shape = shape.cut(box)
        print('  cut %s' % c['name'])

    return shape.removeSplitter()


shape = build()
bb = shape.BoundBox
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
