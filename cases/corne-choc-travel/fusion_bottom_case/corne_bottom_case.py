"""
Typeractive Corne Choc bottom case - parametric rebuild.

Builds the case as native Fusion features (sketch -> extrude -> shell ->
cut), so everything stays editable in the timeline. Nothing here is a mesh
and nothing needs Fusion's subscription-gated Mesh Convert.

Shape was measured off case-bottom-3dp-meshopt.stl; see
typeractive_bottom_profile.py for the numbers and how they were checked.
The part is a uniform 1.5 mm shelled tray: one outline extruded 10.43 mm,
shelled with the bottom face removed, plus a rib, 5 screw holes and the
wall cutouts.

Run inside Fusion: Utilities -> Add-Ins -> Scripts and Add-Ins (Shift+S)
-> My Scripts -> corne_bottom_case -> Run.

To add or resize a port, edit CUTOUTS in typeractive_bottom_profile.py and
re-run. Coordinates match the .step files and shift_cutouts.py.

Everything that can fail happens inside run()'s try block, so a failure
always produces a dialog rather than silence. Progress also goes to the
Text Commands palette (View -> Show Text Commands).
"""

import importlib
import os
import sys
import traceback

import adsk.core
import adsk.fusion

# Fusion's internal unit is cm; every number in the profile module is mm.
MM = 0.1

# One user parameter. The case grows UPWARD from a fixed bottom, so the extra
# height lands in the wall band BELOW the sidewall openings, and the openings,
# the plate and the screw holes all rise with it by the same amount. The case
# bottom, the shelled underside and the rib stay put.
#
# It is a real Fusion user parameter, so after the first run it can be edited
# in Modify -> Change Parameters and the model rebuilds without re-running.
HEIGHT_PARAM = 'case_extra_height'
HEIGHT_DEFAULT_MM = 0.0

# The STL is authored with the floor plate at the TOP, so the part arrives
# upside down. Fusion z is therefore plate_top - mesh_y, which stands the case
# on its floor at z = 0.
#
# Negating z also fixes a mirroring bug. The previous mapping just swapped the
# mesh Y and Z axes onto Fusion Z and Y, and a bare axis swap has determinant
# -1 -- so the body in Fusion was a mirror image of the STL rather than a
# rotation of it. Negating one axis restores determinant +1.
#
# In this frame, for the stock profile:
#   floor   z  0.000 .. 1.498
#   rim     z 10.432                  (open top edge of the wall)
#   rib top z 16.497
#   usb_port  z 3.792 .. 7.692        (2.740 below the rim)
#   side_port z 6.932 .. 10.432       (flush with the rim -- a notch)

# Which end the openings are pinned to as the wall grows.
#   'rim'   -> openings keep their distance below the rim and travel up with
#              it; the wall band BELOW them grows.
#   'floor' -> openings keep their height above the floor; the wall band
#              ABOVE them grows.
OPENING_ANCHOR = 'rim'


def log(msg):
    """Write to the Text Commands palette. Never raises."""
    try:
        adsk.core.Application.log('[corne_bottom_case] %s' % msg)
    except Exception:
        pass


def load_profile():
    """Import the sibling profile module, reloading so edits to CUTOUTS take
    effect without restarting Fusion (Fusion caches imported modules)."""
    here = os.path.dirname(os.path.abspath(__file__))
    if here not in sys.path:
        sys.path.insert(0, here)
    mod_path = os.path.join(here, 'typeractive_bottom_profile.py')
    if not os.path.isfile(mod_path):
        raise RuntimeError('profile module not found next to the script:\n%s'
                           % mod_path)
    import typeractive_bottom_profile as prof
    importlib.reload(prof)
    return prof


def vi(mm):
    return adsk.core.ValueInput.createByReal(mm * MM)


def vs(expr):
    """ValueInput from an expression string. Fusion parses these against the
    parameter table, so an expression may reference user parameters by name."""
    return adsk.core.ValueInput.createByString(expr)


def plus_param(mm):
    """'<mm> mm + <param>' -- a length that tracks the user parameter."""
    return vs('%.4f mm + %s' % (mm, HEIGHT_PARAM))


def pt(x_mm, y_mm, z_mm=0.0):
    return adsk.core.Point3D.create(x_mm * MM, y_mm * MM, z_mm * MM)


def extent_dist(mm):
    """ExtrudeFeatureInput has no setDistanceExtent -- that is the legacy
    API. A distance extent is a DistanceExtentDefinition plus a direction."""
    return adsk.fusion.DistanceExtentDefinition.create(vi(abs(mm)))


def plane_at_z(root, z_mm, name):
    """Horizontal construction plane. The XY plane's normal is +Z, so the
    offset sign is unambiguous."""
    ci = root.constructionPlanes.createInput()
    ci.setByOffset(root.xYConstructionPlane, vi(z_mm))
    p = root.constructionPlanes.add(ci)
    p.name = name
    return p


def plane_at_expr(root, expr, name):
    """Horizontal construction plane whose offset is an expression, so it
    tracks the user parameter."""
    ci = root.constructionPlanes.createInput()
    ci.setByOffset(root.xYConstructionPlane, expr)
    p = root.constructionPlanes.add(ci)
    p.name = name
    return p


def ensure_parameter(design, name, default_mm, comment):
    """Create the user parameter unless it already exists."""
    existing = design.userParameters.itemByName(name)
    if existing is not None:
        return existing
    return design.userParameters.add(
        name, vs('%.4f mm' % default_mm), 'mm', comment)


def cutout_plan(c, wall_t, z_mm):
    """Plan-view footprint of an opening: across the wall, by its width.

    The vertical extent is deliberately NOT in the sketch. It lives in the
    extrude's start offset and depth, which are real feature parameters and so
    can be driven by an expression; sketch geometry cannot be without adding
    driven dimensions. That is what lets the openings ride up with the
    parameter.

    mesh (X, Z, Y) -> Fusion (X, Y, Z), so a +/-X wall opening spans Fusion X
    (through the wall) by Fusion Y (its width), and vice versa.
    """
    half = c['width'] / 2.0
    through = wall_t * 3.0          # comfortably clears the wall both sides
    u = c['along']
    if c['wall'] in ('+X', '-X'):
        return (pt(c['at'] - through, u - half, z_mm),
                pt(c['at'] + through, u + half, z_mm))
    return (pt(u - half, c['at'] - through, z_mm),
            pt(u + half, c['at'] + through, z_mm))


def draw_polygon(sketch, points_mm):
    """Closed polyline from (x, z) mesh pairs -> sketch (x, y)."""
    lines = sketch.sketchCurves.sketchLines
    pts = [pt(x, z) for x, z in points_mm]
    n = len(pts)
    sketch.isComputeDeferred = True
    try:
        for i in range(n):
            lines.addByTwoPoints(pts[i], pts[(i + 1) % n])
    finally:
        sketch.isComputeDeferred = False


def all_profiles(sketch):
    coll = adsk.core.ObjectCollection.create()
    for p in sketch.profiles:
        coll.add(p)
    return coll


def largest_profile(sketch):
    best, best_a = None, -1.0
    for p in sketch.profiles:
        try:
            a = p.areaProperties().area
        except Exception:
            continue
        if a > best_a:
            best, best_a = p, a
    return best


def horizontal_faces(body, tol_mm=0.25):
    """Every planar face lying flat, as (z_mm, area, face).

    Identified from the face's own bounding box, not its surface normal: a
    Plane's normal may be flipped relative to the face that uses it (see
    BRepFace.isParamReversed), and Plane.origin is an arbitrary point on the
    plane rather than anywhere near the face. The bounding box is neither.
    """
    out = []
    for f in body.faces:
        if adsk.core.Plane.cast(f.geometry) is None:
            continue
        bb = f.boundingBox
        zmin, zmax = bb.minPoint.z / MM, bb.maxPoint.z / MM
        if abs(zmax - zmin) <= tol_mm:
            out.append((zmin, f.area / (MM * MM), f))
    return out


def find_rim_face(body, tol_mm=0.25):
    """The open top edge of the wall: the highest flat face.

    Found by height rather than by a fixed value, because the rim rises with
    the parameter. Safe to call only before the rib is added -- the rib's top
    is higher still.
    """
    flats = horizontal_faces(body, tol_mm)
    if not flats:
        return None
    top = max(t[0] for t in flats)
    at_top = [t for t in flats if abs(t[0] - top) <= tol_mm]
    return max(at_top, key=lambda t: t[1])[2]


def build(root, prof):
    L = prof.LEVELS
    feats = root.features
    dir_pos = adsk.fusion.ExtentDirections.PositiveExtentDirection

    datum = L['plate_top']

    def zc(mesh_y):
        """mesh +Y up (floor on top) -> Fusion z, floor down at z = 0."""
        return datum - mesh_y

    floor_bottom = zc(L['plate_top'])        # 0.000
    rim = zc(L['skirt_bottom'])              # 10.432
    rib_top = zc(L['rib_bottom'])            # 16.497
    floor_thickness = zc(L['plate_bottom'])  # 1.498

    # --- 1. blank: outline extruded from the floor up past the rim ---------
    log('sketching outline (%d points)' % len(prof.PLATE_OUTLINE))
    sk = root.sketches.add(plane_at_z(root, floor_bottom, 'floor_bottom'))
    sk.name = 'outline'
    draw_polygon(sk, prof.PLATE_OUTLINE)
    profile = largest_profile(sk)
    if profile is None:
        raise RuntimeError(
            'the outline sketch produced no closed profile - %d curves'
            % sk.sketchCurves.count)

    ext = feats.extrudeFeatures.createInput(
        profile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    # The floor stays on the build plate; the wall grows upward.
    ext.setOneSideExtent(
        adsk.fusion.DistanceExtentDefinition.create(plus_param(rim)), dir_pos)
    body = feats.extrudeFeatures.add(ext).bodies.item(0)
    body.name = 'BottomCase'
    log('blank extruded to rim %.3f mm + %s, %d faces'
        % (rim, HEIGHT_PARAM, body.faces.count))

    # --- 2. shell, opening the top ----------------------------------------
    face = find_rim_face(body)
    if face is None:
        found = ', '.join('z=%.3f (%.0f mm2)' % (z, a)
                          for z, a, _ in sorted(horizontal_faces(body)))
        raise RuntimeError('no flat face to shell.\nFlat faces: %s'
                           % (found or 'none'))
    rm = adsk.core.ObjectCollection.create()
    rm.add(face)
    sh = feats.shellFeatures.createInput(rm, False)
    sh.insideThickness = vi(prof.WALL_THICKNESS)
    feats.shellFeatures.add(sh)
    log('shelled at %.2f mm, top open' % prof.WALL_THICKNESS)

    # --- 3. rib, sitting on the rim and rising with it ---------------------
    sk_rib = root.sketches.add(
        plane_at_expr(root, plus_param(rim), 'rib_base'))
    sk_rib.name = 'rib'
    draw_polygon(sk_rib, prof.RIB_OUTLINE)
    rib_profile = largest_profile(sk_rib)
    if rib_profile is not None:
        ri = feats.extrudeFeatures.createInput(
            rib_profile, adsk.fusion.FeatureOperations.JoinFeatureOperation)
        ri.setOneSideExtent(extent_dist(rib_top - rim), dir_pos)
        feats.extrudeFeatures.add(ri)
        log('rib joined, %.3f mm tall' % (rib_top - rim))

    # --- 4. screw holes through the floor ----------------------------------
    # The floor does not move, so these need no parameter.
    sk_h = root.sketches.add(plane_at_z(root, floor_bottom, 'floor_holes'))
    sk_h.name = 'screw_holes'
    for x, z, r in prof.SCREW_HOLES:
        sk_h.sketchCurves.sketchCircles.addByCenterRadius(pt(x, z), r * MM)
    if sk_h.profiles.count:
        hi = feats.extrudeFeatures.createInput(
            all_profiles(sk_h),
            adsk.fusion.FeatureOperations.CutFeatureOperation)
        hi.setOneSideExtent(extent_dist(floor_thickness + 1.0), dir_pos)
        feats.extrudeFeatures.add(hi)
        log('%d screw holes cut through the floor' % len(prof.SCREW_HOLES))

    # --- 5. wall openings ---------------------------------------------------
    made = []
    for c in prof.CUTOUTS:
        # Underside of the opening in the corrected frame.
        z_bottom = zc(c['y'] + c['height'] / 2.0)
        if OPENING_ANCHOR == 'rim':
            # Pinned below the rim, so it travels up as the wall grows and the
            # gap above it stays constant.
            expr, note = plus_param(z_bottom), '+ %s' % HEIGHT_PARAM
        else:
            # Pinned above the floor, so the wall above it grows instead.
            expr, note = vi(z_bottom), '(fixed)'
        cp = plane_at_expr(root, expr, 'base_%s' % c['name'])
        sk_c = root.sketches.add(cp)
        sk_c.name = 'cutout_%s' % c['name']
        lo3, hi3 = cutout_plan(c, prof.WALL_THICKNESS, z_bottom)
        sk_c.sketchCurves.sketchLines.addTwoPointRectangle(
            sk_c.modelToSketchSpace(lo3), sk_c.modelToSketchSpace(hi3))
        p = largest_profile(sk_c)
        if p is None:
            log('cutout %s: no profile, skipped' % c['name'])
            continue
        ci = feats.extrudeFeatures.createInput(
            p, adsk.fusion.FeatureOperations.CutFeatureOperation)
        ci.setOneSideExtent(extent_dist(c['height']), dir_pos)
        feats.extrudeFeatures.add(ci)
        made.append(c['name'])
        log('cutout %s: z %.3f %s, height %.3f, %.3f below the rim'
            % (c['name'], z_bottom, note, c['height'],
               rim - (z_bottom + c['height'])))

    return body, made


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        log('start')

        prof = load_profile()
        log('profile loaded: %d outline pts, %d holes, %d cutouts'
            % (len(prof.PLATE_OUTLINE), len(prof.SCREW_HOLES),
               len(prof.CUTOUTS)))

        doc = app.documents.add(
            adsk.core.DocumentTypes.FusionDesignDocumentType)
        design = adsk.fusion.Design.cast(app.activeProduct)
        if design is None:
            raise RuntimeError('the new document is not a Design')
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        doc.name = 'Corne Choc bottom case'
        # The root component's name is derived from the document and is not
        # settable -- assigning it raises "root component name cannot be
        # changed". The document name above is what shows in the browser.
        root = design.rootComponent

        ensure_parameter(
            design, HEIGHT_PARAM, HEIGHT_DEFAULT_MM,
            'Extra case height. Added to the main extrusion and to the height '
            'of each sidewall opening above the case bottom, so the wall band '
            'below the openings grows and everything above it rises with it.')
        log('user parameter %s ready' % HEIGHT_PARAM)

        body, made = build(root, prof)
        log('done')

        ui.messageBox(
            'Corne Choc bottom case built.\n\n'
            '  bodies:   %d\n'
            '  faces:    %d\n'
            '  volume:   %.1f mm^3   (mesh measures 19187.7)\n'
            '  cutouts:  %s\n\n'
            'Everything is a timeline feature. To move or resize a port,\n'
            'edit CUTOUTS in typeractive_bottom_profile.py and re-run, or\n'
            'just drag the sketch rectangle.'
            % (root.bRepBodies.count, body.faces.count, body.volume * 1000.0,
               ', '.join(made) if made else 'none'))

    except Exception:
        tb = traceback.format_exc()
        log('FAILED\n%s' % tb)
        if ui:
            ui.messageBox('Failed:\n%s' % tb)
        else:
            raise
