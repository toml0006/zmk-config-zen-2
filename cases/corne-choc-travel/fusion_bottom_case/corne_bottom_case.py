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


def find_bottom_face(body, z_mm, tol_mm=0.25):
    """Planar face pointing -Z at the given height. Fusion geometry objects
    are SWIG proxies, so cast rather than isinstance."""
    for f in body.faces:
        g = adsk.core.Plane.cast(f.geometry)
        if g is None or g.normal.z > -0.99:
            continue
        if abs(g.origin.z / MM - z_mm) < tol_mm:
            return f
    return None


def build(root, prof):
    L = prof.LEVELS
    feats = root.features
    top, bot = L['plate_top'], L['skirt_bottom']
    dir_pos = adsk.fusion.ExtentDirections.PositiveExtentDirection
    dir_neg = adsk.fusion.ExtentDirections.NegativeExtentDirection

    # --- 1. tray blank: outline extruded the full height -------------------
    log('sketching outline (%d points)' % len(prof.PLATE_OUTLINE))
    sk = root.sketches.add(plane_at_z(root, bot, 'skirt_bottom'))
    sk.name = 'outline'
    draw_polygon(sk, prof.PLATE_OUTLINE)
    profile = largest_profile(sk)
    if profile is None:
        raise RuntimeError(
            'the outline sketch produced no closed profile - %d curves'
            % sk.sketchCurves.count)

    ext = feats.extrudeFeatures.createInput(
        profile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    ext.setOneSideExtent(extent_dist(top - bot), dir_pos)
    body = feats.extrudeFeatures.add(ext).bodies.item(0)
    body.name = 'BottomCase'
    log('blank extruded, %d faces' % body.faces.count)

    # --- 2. shell it, removing the open underside --------------------------
    face = find_bottom_face(body, bot)
    if face is None:
        raise RuntimeError('could not identify the bottom face to shell')
    rm = adsk.core.ObjectCollection.create()
    rm.add(face)
    sh = feats.shellFeatures.createInput(rm, False)
    sh.insideThickness = vi(prof.WALL_THICKNESS)
    feats.shellFeatures.add(sh)
    log('shelled at %.2f mm' % prof.WALL_THICKNESS)

    # --- 3. rib below the skirt -------------------------------------------
    sk_rib = root.sketches.add(plane_at_z(root, L['rib_bottom'], 'rib_bottom'))
    sk_rib.name = 'rib'
    draw_polygon(sk_rib, prof.RIB_OUTLINE)
    rib_profile = largest_profile(sk_rib)
    if rib_profile is not None:
        ri = feats.extrudeFeatures.createInput(
            rib_profile, adsk.fusion.FeatureOperations.JoinFeatureOperation)
        ri.setOneSideExtent(
            extent_dist(L['skirt_bottom'] - L['rib_bottom']), dir_pos)
        feats.extrudeFeatures.add(ri)
        log('rib joined')

    # --- 4. screw holes through the plate ---------------------------------
    sk_h = root.sketches.add(plane_at_z(root, top, 'plate_top'))
    sk_h.name = 'screw_holes'
    for x, z, r in prof.SCREW_HOLES:
        sk_h.sketchCurves.sketchCircles.addByCenterRadius(pt(x, z), r * MM)
    if sk_h.profiles.count:
        hi = feats.extrudeFeatures.createInput(
            all_profiles(sk_h),
            adsk.fusion.FeatureOperations.CutFeatureOperation)
        hi.setOneSideExtent(extent_dist((top - bot) + 1.0), dir_neg)
        feats.extrudeFeatures.add(hi)
        log('%d screw holes cut' % len(prof.SCREW_HOLES))

    # --- 5. wall cutouts ---------------------------------------------------
    made = []
    for c in prof.CUTOUTS:
        axis = 'x' if c['wall'] in ('+X', '-X') else 'y'
        cp = wall_plane(root, axis, c['at'], 'wall_%s' % c['name'])
        sk_c = root.sketches.add(cp)
        sk_c.name = 'cutout_%s' % c['name']
        u, v = c['along'], c['y']
        w, h = c['width'] / 2.0, c['height'] / 2.0
        sk_c.sketchCurves.sketchLines.addTwoPointRectangle(
            pt(u - w, v - h), pt(u + w, v + h))
        p = largest_profile(sk_c)
        if p is None:
            log('cutout %s: no profile, skipped' % c['name'])
            continue
        ci = feats.extrudeFeatures.createInput(
            p, adsk.fusion.FeatureOperations.CutFeatureOperation)
        # Symmetric, so it cuts the wall whichever way the plane faces.
        ci.setSymmetricExtent(vi(prof.WALL_THICKNESS * 6), True)
        feats.extrudeFeatures.add(ci)
        made.append(c['name'])
        log('cutout %s cut' % c['name'])

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
