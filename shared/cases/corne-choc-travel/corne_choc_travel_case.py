"""
Corne Choc travel case — Fusion 360 script.

Form-fit pockets that follow the Corne half outline (main key cluster +
thumb cluster bulge). Both halves are rotated 90 degrees so the overall
case fits within a 250 x 250 mm printer build plate.

Run inside Fusion: Utilities -> Add-Ins -> Scripts and Add-Ins -> Scripts
-> + (My Scripts) -> select this folder -> Run.

All dimensions in millimeters. Tune the params block to match your build.
"""

import adsk.core
import adsk.fusion
import math
import traceback

# --------------------------------------------------------------------------
# PARAMETERS
# --------------------------------------------------------------------------
PARAMS = {
    # Corne Choc half outline. Extracted from the Typeractive Corne Choc
    # bottom-case STL (case-bottom-3dp-meshopt.stl, rim faces at Y=3.5).
    # Outline traces the inner rim where the PCB sits — this is the
    # cavity the keyboard half drops into. Bbox 131.7 x 87.2 mm.
    #
    # Origin at outline min corner, +x right, +y down. Polygon order
    # comes from boundary walk (mixed CW/CCW). Script handles either.
    #
    # See typeractive_outline.py for extraction source + holes, and
    # typeractive_outline.png for visual reference.
    'half_outline_mm': [
        (1.939, 25.658), (56.248, 25.650), (64.807, 13.936),
        (65.236, 13.774), (65.812, 13.417), (98.771, 8.964),
        (113.649, 0.397), (114.541, 0.000), (114.963, 0.178),
        (115.944, 0.422), (116.853, 0.836), (117.494, 1.606),
        (131.430, 25.683), (131.706, 26.770), (131.657, 80.519),
        (131.260, 81.347), (130.757, 82.004), (129.735, 82.418),
        (93.937, 82.426), (93.750, 83.318), (93.491, 83.870),
        (92.979, 84.511), (91.990, 84.908), (75.944, 84.940),
        (75.587, 86.003), (74.898, 86.822), (73.989, 87.163),
        (57.319, 87.187), (56.354, 86.790), (55.672, 86.019),
        (55.348, 84.973), (39.270, 84.916), (38.459, 84.697),
        (37.826, 84.016), (37.437, 83.091), (37.494, 80.122),
        (1.890, 80.163), (1.055, 79.944), (0.649, 79.400),
        (0.203, 79.067), (0.008, 78.240), (0.000, 27.556),
        (0.227, 26.705), (0.771, 26.299), (1.103, 25.853),
    ],

    # Mounting hole positions from the Typeractive case (same source).
    # (center_x, center_y, radius_mm). Drilled through the tray floor at
    # each pocket's local coords, mirrored for the right pocket. Set to
    # [] to disable mounting holes entirely.
    'mounting_holes_mm': [
        (92.802, 64.785, 1.468),
        (106.155, 23.052, 1.458),
        (20.381, 44.528, 1.446),
        (61.419, 29.835, 1.473),
        (20.539, 61.586, 1.472),
    ],

    # Pocket-to-half clearance (per side) — accounts for print tolerance.
    'pocket_clearance':  1.0,

    # Assembled stack height of one half (plate + PCB + switches + caps).
    'stack_height':      22.0,

    # Rotation applied to each half before placing in the tray.
    # Positive = CCW. Halves end up portrait (long dim vertical).
    'rotation_deg':      90.0,

    # Gap between the two halves inside the tray (between pocket bboxes).
    'inner_gap':         15.0,

    # Border around the pockets (wall thickness on all sides).
    'border':            10.0,

    # Tray floor thickness below the pocket.
    'floor_thickness':    4.0,

    # Lid thickness.
    'lid_thickness':      5.0,

    # Foam pocket in lid (0 for none).
    'lid_foam_depth':     3.0,
    'lid_foam_inset':     4.0,

    # Outer body corner fillet.
    'corner_radius':     8.0,

    # M3 corner bolt holes.
    'bolt_hole_dia':     3.4,
    'bolt_hole_inset':   6.0,

    # Lid drawn alongside tray for visibility (+Y offset, mm).
    'lid_y_offset':      40.0,

    # Sanity check: max build-plate envelope (mm).
    'build_plate':       (250.0, 250.0),
}


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------
def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface

        # Fresh document.
        app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        design = app.activeProduct
        root = design.rootComponent

        p = PARAMS

        # Compute transformed half outlines (left + right) and tray size.
        (left_poly, right_poly, left_holes, right_holes,
         pocket_bbox) = _compute_pocket_polygons(p)
        bbox_w, bbox_d = pocket_bbox

        tray_w = bbox_w + (2 * p['border'])
        tray_d = bbox_d + (2 * p['border'])
        tray_h = p['stack_height'] + p['floor_thickness']

        plate_w, plate_d = p['build_plate']
        if tray_w > plate_w or tray_d > plate_d:
            raise RuntimeError(
                f'Tray {tray_w:.1f} x {tray_d:.1f} exceeds build plate '
                f'{plate_w:.0f} x {plate_d:.0f}. Reduce border / clearance.'
            )

        # Shift polygons + hole centers by border so they sit inside the tray.
        b = p['border']
        left_poly = _translate(left_poly, b, b)
        right_poly = _translate(right_poly, b, b)
        left_holes = [(x + b, y + b, r) for x, y, r in left_holes]
        right_holes = [(x + b, y + b, r) for x, y, r in right_holes]

        # Tray.
        tray_comp = _new_component(root, 'TrayBase')
        _build_tray(tray_comp, p, tray_w, tray_d, tray_h,
                    left_poly, right_poly, left_holes + right_holes)

        # Lid (drawn +Y for visibility).
        lid_comp = _new_component(root, 'Lid')
        _build_lid(lid_comp, p, tray_w, tray_d,
                   p['lid_y_offset'] + tray_d)

        ui.messageBox(
            'Corne Choc travel case generated.\n'
            f'Tray: {tray_w:.1f} x {tray_d:.1f} x {tray_h:.1f} mm\n'
            f'Lid:  {tray_w:.1f} x {tray_d:.1f} x {p["lid_thickness"]:.1f} mm\n'
            f'Build plate budget: {plate_w:.0f} x {plate_d:.0f} mm\n\n'
            'Adjust PARAMS and re-run to tweak.'
        )

    except Exception:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


# --------------------------------------------------------------------------
# Polygon transforms
# --------------------------------------------------------------------------
def _compute_pocket_polygons(p):
    """Rotate, offset (clearance), mirror, and pack two half outlines.

    Returns:
        left_poly, right_poly: polygon vertex lists, in tray-local mm coords
            (pre-border shift).
        left_holes, right_holes: lists of (cx, cy, radius) for mounting
            holes, transformed to match.
        pocket_bbox: (width, height) of the side-by-side pocket pair.
    """
    base = p['half_outline_mm']
    holes_in = p.get('mounting_holes_mm', [])
    rot = math.radians(p['rotation_deg'])

    # 1. Rotate polygon + hole centers by the same angle.
    rotated_poly = _rotate(base, rot)
    rotated_holes = _rotate([(h[0], h[1]) for h in holes_in], rot)
    hole_radii = [h[2] for h in holes_in]

    # 2. Normalize: find the polygon's min corner, shift both polygon and
    # hole centers by the same offset.
    xs = [p[0] for p in rotated_poly]
    ys = [p[1] for p in rotated_poly]
    minx, miny = min(xs), min(ys)
    norm_poly = [(x - minx, y - miny) for x, y in rotated_poly]
    norm_holes = [(x - minx, y - miny) for x, y in rotated_holes]

    # 3. Clearance: inflate polygon vertices outward from centroid.
    # Hole positions are unchanged — they're absolute landmarks.
    clear = p['pocket_clearance']
    inflated = _expand_from_centroid(norm_poly, clear)
    # Re-normalize after inflation; apply same delta to holes.
    ixs = [p[0] for p in inflated]; iys = [p[1] for p in inflated]
    dx, dy = min(ixs), min(iys)
    inflated = [(x - dx, y - dy) for x, y in inflated]
    shifted_holes = [(x - dx, y - dy) for x, y in norm_holes]
    w = max(p[0] for p in inflated)
    h = max(p[1] for p in inflated)

    # 4. Mirror across vertical axis for the right half (polygon + holes).
    mirrored_poly = _mirror_x(inflated, w)
    mirrored_holes = [(w - x, y) for x, y in shifted_holes]

    # 5. Place side-by-side. Left at (0,0). Right at (w + gap, 0).
    gap = p['inner_gap']
    right_poly = _translate(mirrored_poly, w + gap, 0.0)
    right_holes_xy = [(x + w + gap, y) for x, y in mirrored_holes]

    left_holes = list(zip(*([h[0] for h in shifted_holes],
                            [h[1] for h in shifted_holes],
                            hole_radii)))
    right_holes = list(zip(*([h[0] for h in right_holes_xy],
                             [h[1] for h in right_holes_xy],
                             hole_radii)))

    pocket_bbox = (2 * w + gap, h)
    return inflated, right_poly, left_holes, right_holes, pocket_bbox


def _rotate(pts, theta):
    c, s = math.cos(theta), math.sin(theta)
    return [(x * c - y * s, x * s + y * c) for (x, y) in pts]


def _normalize(pts):
    xs = [x for x, _ in pts]
    ys = [y for _, y in pts]
    minx, miny = min(xs), min(ys)
    shifted = [(x - minx, y - miny) for (x, y) in pts]
    return shifted, (max(xs) - minx, max(ys) - miny)


def _mirror_x(pts, width):
    return [(width - x, y) for (x, y) in pts]


def _translate(pts, dx, dy):
    return [(x + dx, y + dy) for (x, y) in pts]


def _expand_from_centroid(pts, delta):
    cx = sum(x for x, _ in pts) / len(pts)
    cy = sum(y for _, y in pts) / len(pts)
    out = []
    for x, y in pts:
        vx, vy = x - cx, y - cy
        d = math.hypot(vx, vy)
        if d == 0:
            out.append((x, y))
            continue
        out.append((x + vx / d * delta, y + vy / d * delta))
    return out


# --------------------------------------------------------------------------
# Fusion geometry
# --------------------------------------------------------------------------
def _new_component(root, name):
    occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp = occ.component
    comp.name = name
    return comp


def _build_tray(comp, p, tray_w, tray_d, tray_h, left_poly, right_poly,
                mounting_holes):
    sketches = comp.sketches
    xy_plane = comp.xYConstructionPlane

    # Outer rectangle (mm -> cm).
    sk = sketches.add(xy_plane)
    sk.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(0, 0, 0),
        adsk.core.Point3D.create(tray_w / 10.0, tray_d / 10.0, 0),
    )

    prof = sk.profiles.item(0)
    extrudes = comp.features.extrudeFeatures
    ext = extrudes.createInput(
        prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    ext.setDistanceExtent(
        False, adsk.core.ValueInput.createByReal(tray_h / 10.0))
    body = extrudes.add(ext).bodies.item(0)

    _fillet_vertical_edges(comp, body, p['corner_radius'] / 10.0)

    # Pocket cutouts.
    top_face = _find_top_face(body, tray_h / 10.0)
    pocket_sketch = sketches.add(top_face)
    _draw_polygon(pocket_sketch, left_poly)
    _draw_polygon(pocket_sketch, right_poly)

    pocket_depth = p['stack_height'] / 10.0
    for i in range(pocket_sketch.profiles.count):
        prof_i = pocket_sketch.profiles.item(i)
        cut = extrudes.createInput(
            prof_i, adsk.fusion.FeatureOperations.CutFeatureOperation)
        cut.setDistanceExtent(
            False, adsk.core.ValueInput.createByReal(-pocket_depth))
        cut.participantBodies = [body]
        extrudes.add(cut)

    _add_corner_holes(comp, body, tray_w, tray_d, tray_h,
                      p['bolt_hole_dia'], p['bolt_hole_inset'])

    # Mounting holes (drilled through the entire tray floor).
    if mounting_holes:
        _drill_holes(comp, body, tray_h, mounting_holes)


def _drill_holes(comp, body, tray_h, holes):
    """Drill a set of (cx, cy, radius_mm) holes through the tray top face."""
    top_face = _find_top_face(body, tray_h / 10.0)
    if not top_face:
        return
    sk = comp.sketches.add(top_face)
    circles = sk.sketchCurves.sketchCircles
    for cx, cy, r in holes:
        circles.addByCenterRadius(
            adsk.core.Point3D.create(cx / 10.0, cy / 10.0, 0),
            r / 10.0,
        )
    extrudes = comp.features.extrudeFeatures
    for i in range(sk.profiles.count):
        prof = sk.profiles.item(i)
        cut = extrudes.createInput(
            prof, adsk.fusion.FeatureOperations.CutFeatureOperation)
        cut.setDistanceExtent(
            False, adsk.core.ValueInput.createByReal(-tray_h / 10.0))
        cut.participantBodies = [body]
        extrudes.add(cut)


def _build_lid(comp, p, tray_w, tray_d, y_offset_mm):
    sketches = comp.sketches
    xy_plane = comp.xYConstructionPlane

    sk = sketches.add(xy_plane)
    y0 = y_offset_mm / 10.0
    sk.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(0, y0, 0),
        adsk.core.Point3D.create(tray_w / 10.0, y0 + tray_d / 10.0, 0),
    )

    prof = sk.profiles.item(0)
    extrudes = comp.features.extrudeFeatures
    ext = extrudes.createInput(
        prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    ext.setDistanceExtent(
        False, adsk.core.ValueInput.createByReal(p['lid_thickness'] / 10.0))
    body = extrudes.add(ext).bodies.item(0)

    _fillet_vertical_edges(comp, body, p['corner_radius'] / 10.0)

    if p['lid_foam_depth'] > 0:
        top_face = _find_top_face(body, p['lid_thickness'] / 10.0)
        sk_foam = sketches.add(top_face)
        inset = p['lid_foam_inset'] / 10.0
        sk_foam.sketchCurves.sketchLines.addTwoPointRectangle(
            adsk.core.Point3D.create(inset, y0 + inset, 0),
            adsk.core.Point3D.create(
                tray_w / 10.0 - inset, y0 + tray_d / 10.0 - inset, 0),
        )
        cut = extrudes.createInput(
            sk_foam.profiles.item(0),
            adsk.fusion.FeatureOperations.CutFeatureOperation)
        cut.setDistanceExtent(
            False,
            adsk.core.ValueInput.createByReal(-p['lid_foam_depth'] / 10.0))
        cut.participantBodies = [body]
        extrudes.add(cut)

    _add_corner_holes(
        comp, body, tray_w, tray_d, p['lid_thickness'],
        p['bolt_hole_dia'], p['bolt_hole_inset'],
        y_offset_mm=y_offset_mm)


def _draw_polygon(sketch, points_mm):
    lines = sketch.sketchCurves.sketchLines
    cm = [(x / 10.0, y / 10.0) for (x, y) in points_mm]
    for i in range(len(cm)):
        a = cm[i]
        b = cm[(i + 1) % len(cm)]
        lines.addByTwoPoints(
            adsk.core.Point3D.create(a[0], a[1], 0),
            adsk.core.Point3D.create(b[0], b[1], 0),
        )


def _find_top_face(body, height_cm, tol=1e-3):
    for face in body.faces:
        if face.geometry.objectType == adsk.core.Plane.classType():
            origin = face.pointOnFace
            if abs(origin.z - height_cm) < tol:
                return face
    return None


def _fillet_vertical_edges(comp, body, radius_cm):
    if radius_cm <= 0:
        return
    fillets = comp.features.filletFeatures
    edges = adsk.core.ObjectCollection.create()
    for edge in body.edges:
        sv = edge.startVertex.geometry
        ev = edge.endVertex.geometry
        if abs(sv.z - ev.z) > 1e-3:
            edges.add(edge)
    if edges.count == 0:
        return
    fin = fillets.createInput()
    fin.addConstantRadiusEdgeSet(
        edges, adsk.core.ValueInput.createByReal(radius_cm), True)
    try:
        fillets.add(fin)
    except Exception:
        pass  # tolerate failures on tight corners


def _add_corner_holes(comp, body, tray_w, tray_d, tray_h,
                      dia_mm, inset_mm, y_offset_mm=0.0):
    sketches = comp.sketches
    top_face = _find_top_face(body, tray_h / 10.0)
    if not top_face:
        return
    sk = sketches.add(top_face)

    inset = inset_mm / 10.0
    w = tray_w / 10.0
    d = tray_d / 10.0
    y0 = y_offset_mm / 10.0
    r = (dia_mm / 2.0) / 10.0

    centers = [
        (inset, y0 + inset),
        (w - inset, y0 + inset),
        (inset, y0 + d - inset),
        (w - inset, y0 + d - inset),
    ]
    circles = sk.sketchCurves.sketchCircles
    for cx, cy in centers:
        circles.addByCenterRadius(
            adsk.core.Point3D.create(cx, cy, 0), r)

    extrudes = comp.features.extrudeFeatures
    for i in range(sk.profiles.count):
        prof = sk.profiles.item(i)
        cut = extrudes.createInput(
            prof, adsk.fusion.FeatureOperations.CutFeatureOperation)
        cut.setDistanceExtent(
            False, adsk.core.ValueInput.createByReal(-tray_h / 10.0))
        cut.participantBodies = [body]
        extrudes.add(cut)
