"""
Typeractive Corne Choc bottom case — parametric rebuild.

Builds the case as native Fusion features (sketch -> extrude -> shell ->
cut), so everything stays editable in the timeline. Nothing here is a mesh
and nothing needs Fusion's subscription-gated Mesh Convert.

Why a rebuild instead of a conversion: mesh -> B-Rep conversion either needs
the gated Prismatic converter, or produces one B-Rep face per triangle
(2078 faces for this STL) which cannot be push/pulled or filleted.

Shape was measured off case-bottom-3dp-meshopt.stl -- see
typeractive_bottom_profile.py for the numbers and how they were checked.
The part is a uniform 1.5 mm shelled tray: one outline extruded 10.43 mm,
shelled with the bottom face removed, plus a rib, 5 screw holes and the
wall cutouts.

Run inside Fusion: Utilities -> Add-Ins -> Scripts and Add-Ins (Shift+S)
-> My Scripts -> corne_bottom_case -> Run.

To add or resize a port, edit CUTOUTS in typeractive_bottom_profile.py and
re-run. Coordinates match the .step files and shift_cutouts.py.
"""

import traceback

import adsk.core
import adsk.fusion

import typeractive_bottom_profile as prof

# Fusion's internal unit is cm; every number in the profile module is mm.
MM = 0.1


def extent_dist(mm):
    """ExtrudeFeatureInput has no setDistanceExtent -- that is the legacy API.
    A distance extent is a DistanceExtentDefinition plus a direction."""
    return adsk.fusion.DistanceExtentDefinition.create(vi(abs(mm)))


DIR_POS = adsk.fusion.ExtentDirections.PositiveExtentDirection
DIR_NEG = adsk.fusion.ExtentDirections.NegativeExtentDirection


def vi(mm):
    return adsk.core.ValueInput.createByReal(mm * MM)


def pt(x_mm, y_mm, z_mm=0.0):
    return adsk.core.Point3D.create(x_mm * MM, y_mm * MM, z_mm * MM)


def plane_at_z(root, z_mm, name):
    """Horizontal construction plane. XY plane normal is +Z, so the offset
    sign is unambiguous."""
    ci = root.constructionPlanes.createInput()
    ci.setByOffset(root.xYConstructionPlane, vi(z_mm))
    p = root.constructionPlanes.add(ci)
    p.name = name
    return p


def wall_plane(root, axis, at_mm, name):
    """Vertical construction plane through a wall, pinned by three explicit
    points so its position never depends on a normal-direction convention.
    Cutout rectangles are centred, so a mirrored local frame is harmless."""
    if axis == 'x':
        p1, p2, p3 = pt(at_mm, 0, 0), pt(at_mm, 10, 0), pt(at_mm, 0, 10)
    else:
        p1, p2, p3 = pt(0, at_mm, 0), pt(10, at_mm, 0), pt(0, at_mm, 10)
    ci = root.constructionPlanes.createInput()
    ci.setByThreePoints(p1, p2, p3)
    p = root.constructionPlanes.add(ci)
    p.name = name
    return p


def draw_polygon(sketch, points_mm):
    """Closed polyline from (x, z) mesh pairs -> sketch (x, y)."""
    lines = sketch.sketchCurves.sketchLines
    n = len(points_mm)
    pts = [pt(x, z) for x, z in points_mm]
    for i in range(n):
        lines.addByTwoPoints(pts[i], pts[(i + 1) % n])


def all_profiles(sketch):
    coll = adsk.core.ObjectCollection.create()
    for p in sketch.profiles:
        coll.add(p)
    return coll


def largest_profile(sketch):
    best, best_a = None, -1.0
    for p in sketch.profiles:
        a = p.areaProperties().area
        if a > best_a:
            best, best_a = p, a
    return best


def find_bottom_face(body, z_mm, tol_mm=0.25):
    """Planar face pointing -Z at the given height."""
    for f in body.faces:
        g = adsk.core.Plane.cast(f.geometry)
        if g is None:
            continue
        nz = g.normal.z
        if nz > -0.99:
            continue
        if abs(g.origin.z / MM - z_mm) < tol_mm:
            return f
    return None


def build(root, ui):
    L = prof.LEVELS
    feats = root.features
    top, bot = L['plate_top'], L['skirt_bottom']

    # --- 1. tray blank: outline extruded the full height -------------------
    base_plane = plane_at_z(root, bot, 'skirt_bottom')
    sk = root.sketches.add(base_plane)
    sk.name = 'outline'
    draw_polygon(sk, prof.PLATE_OUTLINE)
    profile = largest_profile(sk)
    if profile is None:
        raise RuntimeError('outline sketch produced no closed profile')

    ext = feats.extrudeFeatures.createInput(
        profile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    ext.setOneSideExtent(extent_dist(top - bot), DIR_POS)
    blank = feats.extrudeFeatures.add(ext)
    body = blank.bodies.item(0)
    body.name = 'BottomCase'

    # --- 2. shell it, removing the open underside --------------------------
    face = find_bottom_face(body, bot)
    if face is None:
        raise RuntimeError('could not identify the bottom face to shell')
    rm = adsk.core.ObjectCollection.create()
    rm.add(face)
    sh = feats.shellFeatures.createInput(rm, False)
    sh.insideThickness = vi(prof.WALL_THICKNESS)
    feats.shellFeatures.add(sh)

    # --- 3. rib below the skirt -------------------------------------------
    rib_plane = plane_at_z(root, L['rib_bottom'], 'rib_bottom')
    sk_rib = root.sketches.add(rib_plane)
    sk_rib.name = 'rib'
    draw_polygon(sk_rib, prof.RIB_OUTLINE)
    rib_profile = largest_profile(sk_rib)
    if rib_profile is not None:
        ri = feats.extrudeFeatures.createInput(
            rib_profile, adsk.fusion.FeatureOperations.JoinFeatureOperation)
        ri.setOneSideExtent(
            extent_dist(L['skirt_bottom'] - L['rib_bottom']), DIR_POS)
        feats.extrudeFeatures.add(ri)

    # --- 4. screw holes through the plate ---------------------------------
    top_plane = plane_at_z(root, top, 'plate_top')
    sk_h = root.sketches.add(top_plane)
    sk_h.name = 'screw_holes'
    for x, z, r in prof.SCREW_HOLES:
        sk_h.sketchCurves.sketchCircles.addByCenterRadius(pt(x, z), r * MM)
    if sk_h.profiles.count:
        hi = feats.extrudeFeatures.createInput(
            all_profiles(sk_h), adsk.fusion.FeatureOperations.CutFeatureOperation)
        hi.setOneSideExtent(extent_dist((top - bot) + 1.0), DIR_NEG)
        feats.extrudeFeatures.add(hi)

    # --- 5. wall cutouts ---------------------------------------------------
    made = []
    for c in prof.CUTOUTS:
        wall = c['wall']
        axis = 'x' if wall in ('+X', '-X') else 'y'
        cp = wall_plane(root, axis, c['at'], 'wall_%s' % c['name'])
        sk_c = root.sketches.add(cp)
        sk_c.name = 'cutout_%s' % c['name']
        u, v = c['along'], c['y']
        w, h = c['width'] / 2.0, c['height'] / 2.0
        sk_c.sketchCurves.sketchLines.addTwoPointRectangle(
            pt(u - w, v - h), pt(u + w, v + h))
        p = largest_profile(sk_c)
        if p is None:
            continue
        ci = feats.extrudeFeatures.createInput(
            p, adsk.fusion.FeatureOperations.CutFeatureOperation)
        # Symmetric so it cuts the wall whichever way the plane faces.
        ci.setSymmetricExtent(vi(prof.WALL_THICKNESS * 6), True)
        feats.extrudeFeatures.add(ci)
        made.append(c['name'])

    return body, made


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface

        doc = app.documents.add(
            adsk.core.DocumentTypes.FusionDesignDocumentType)
        design = adsk.fusion.Design.cast(app.activeProduct)
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        doc.name = 'Corne Choc bottom case'
        root = design.rootComponent
        root.name = 'BottomCase'

        body, made = build(root, ui)

        ui.messageBox(
            'Corne Choc bottom case built.\n\n'
            '  bodies:   %d\n'
            '  faces:    %d\n'
            '  volume:   %.1f mm^3   (mesh measures 19187.7)\n'
            '  cutouts:  %s\n\n'
            'Everything is a timeline feature. To move or resize a port, edit\n'
            'CUTOUTS in typeractive_bottom_profile.py and re-run, or just drag\n'
            'the sketch rectangle.'
            % (root.bRepBodies.count, body.faces.count, body.volume * 1000.0,
               ', '.join(made) if made else 'none'))

    except Exception:
        if ui:
            ui.messageBox('Failed:\n%s' % traceback.format_exc())
