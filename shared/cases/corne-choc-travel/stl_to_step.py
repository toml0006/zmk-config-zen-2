"""
Batch STL -> STEP via FreeCAD CLI.

Usage:
    /Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd \
        stl_to_step.py -- input1.stl input2.stl ...

Output files written next to inputs with .step extension.

Caveat: produces one STEP face per mesh triangle (no prismatic feature
detection). Useful as a B-Rep solid wrapper around mesh geometry, but
NOT well-suited for parametric editing in Fusion. For editable output,
use Fusion's Mesh -> Convert Mesh -> Prismatic instead.
"""

import sys
import os
import Mesh
import Part


def convert(stl_path, sewing_tolerance=0.05):
    out_path = os.path.splitext(stl_path)[0] + '.step'
    print(f'Converting {stl_path} -> {out_path}')

    mesh = Mesh.Mesh(stl_path)
    shape = Part.Shape()
    shape.makeShapeFromMesh(mesh.Topology, sewing_tolerance)
    solid = Part.makeSolid(shape)

    solid.exportStep(out_path)
    print(f'  done. faces: {len(solid.Faces)}, '
          f'volume: {solid.Volume:.1f} mm^3')


def main():
    args = sys.argv[1:]
    if '--' in args:
        args = args[args.index('--') + 1:]
    if not args:
        print('usage: freecadcmd stl_to_step.py -- file1.stl [file2.stl ...]')
        sys.exit(1)
    for path in args:
        try:
            convert(path)
        except Exception as e:
            print(f'  FAILED on {path}: {e}')


if __name__ == '__main__':
    main()
