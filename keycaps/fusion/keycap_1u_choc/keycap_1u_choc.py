# Choc v1 keycap, 1u, Choc-spaced — parametric rebuild
# KEA-like tapered body, SOLID, with a raised cylinder on top whose face is dished.
#
# HOW TO RUN (Fusion 360):
#   Utilities tab > ADD-INS > Scripts and Add-Ins (Shift+S)
#   > Scripts > green "+" > pick this file's folder > Run.
#   Re-run after editing the PARAMETERS block below. Each run makes a new
#   component "Keycap_1u"; prior ones with that name are auto-deleted.
#
# Geometry notes:
#   - Stem = two Choc twin slots (5.7mm pitch, 1.2x3.0mm, r0.3), cut up from bottom.
#   - Optional underside RELIEF pocket clears the switch housing top (set depth 0 to disable).
#   - Cap corners + slot corners rounded via rounded-rect sketches (no fragile edge fillets).
#   - Units in this file are MILLIMETERS; converted to Fusion's internal cm on use.

import adsk.core, adsk.fusion, traceback, math

# ============================ PARAMETERS (mm) ============================
BASE_X       = 17.5   # bottom footprint X (Choc-spaced 1u; 18mm grid - 0.5 gap)
BASE_Y       = 16.5   # bottom footprint Y (17mm grid - 0.5 gap)
TOP_X        = 15.5   # top-of-body footprint X (taper in)
TOP_Y        = 14.6   # top-of-body footprint Y
BODY_H       = 5.0    # height of tapered body (bottom face -> cap top shoulder)
CORNER_R     = 1.2    # cap corner radius

CYL_DIA      = 14.0   # raised cylinder diameter (PARAMETRIC — start "wide")
CYL_H        = 2.0    # raised cylinder height (PARAMETRIC — try 1..3)
DISH_DEPTH   = 1.2    # spherical dish depth at center of the cylinder face

STEM_SLOT_W  = 1.2    # Choc slot width  (along X)
STEM_SLOT_L  = 3.0    # Choc slot length (along Y)
STEM_PITCH   = 5.7    # slot center-to-center (along X)
STEM_DEPTH   = 3.0    # slot depth, cut up from bottom face
STEM_R       = 0.3    # slot corner radius

RELIEF_X     = 13.0   # underside switch-clearance pocket X (set RELIEF_DEPTH=0 to skip)
RELIEF_Y     = 13.0   # underside switch-clearance pocket Y
RELIEF_DEPTH = 2.2    # pocket depth from bottom face
RELIEF_R     = 1.0    # pocket corner radius

COMP_NAME    = "Keycap_1u"
# =========================================================================


def cm(mm):
    return mm * 0.1


def val(mm):
    return adsk.core.ValueInput.createByReal(cm(mm))


def p3(x_mm, y_mm, z_mm=0.0):
    return adsk.core.Point3D.create(cm(x_mm), cm(y_mm), cm(z_mm))


def add_rounded_rect(sketch, cx, cy, w, h, r):
    """Draw a centered rounded rectangle (mm). Falls back to a plain rect if r<=0.
    Coordinates are sketch-local; returns nothing (read sketch.profiles after)."""
    lines = sketch.sketchCurves.sketchLines
    arcs = sketch.sketchCurves.sketchArcs
    r = max(0.0, min(r, (min(w, h) / 2.0) - 1e-4))
    hw, hh = w / 2.0, h / 2.0
    if r <= 0.0:
        lines.addTwoPointRectangle(p3(cx - hw, cy - hh), p3(cx + hw, cy + hh))
        return
    q = math.pi / 2.0
    # tangent points (CCW from bottom of right edge)
    p1 = p3(cx + hw, cy - hh + r)
    p2 = p3(cx + hw, cy + hh - r)
    p3b = p3(cx + hw - r, cy + hh)
    p4 = p3(cx - hw + r, cy + hh)
    p5 = p3(cx - hw, cy + hh - r)
    p6 = p3(cx - hw, cy - hh + r)
    p7 = p3(cx - hw + r, cy - hh)
    p8 = p3(cx + hw - r, cy - hh)
    lines.addByTwoPoints(p1, p2)
    arcs.addByCenterStartSweep(p3(cx + hw - r, cy + hh - r), p2, q)
    lines.addByTwoPoints(p3b, p4)
    arcs.addByCenterStartSweep(p3(cx - hw + r, cy + hh - r), p4, q)
    lines.addByTwoPoints(p5, p6)
    arcs.addByCenterStartSweep(p3(cx - hw + r, cy - hh + r), p6, q)
    lines.addByTwoPoints(p7, p8)
    arcs.addByCenterStartSweep(p3(cx + hw - r, cy - hh + r), p8, q)


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        design = adsk.fusion.Design.cast(app.activeProduct)
        if not design:
            ui.messageBox("Open a Fusion Design first.")
            return
        root = design.rootComponent

        # remove prior runs
        for occ in list(root.occurrences):
            if occ.component.name == COMP_NAME:
                occ.deleteMe()

        occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        comp = occ.component
        comp.name = COMP_NAME
        feats = comp.features

        # --- top construction plane at BODY_H ---
        planes = comp.constructionPlanes
        pin = planes.createInput()
        pin.setByOffset(comp.xYConstructionPlane, val(BODY_H))
        plane_top = planes.add(pin)

        # --- base profile (z=0) ---
        sk_base = comp.sketches.add(comp.xYConstructionPlane)
        sk_base.isComputeDeferred = True
        add_rounded_rect(sk_base, 0, 0, BASE_X, BASE_Y, CORNER_R)
        sk_base.isComputeDeferred = False
        prof_base = sk_base.profiles.item(0)

        # --- top profile (z=BODY_H) ---
        sk_top = comp.sketches.add(plane_top)
        sk_top.isComputeDeferred = True
        add_rounded_rect(sk_top, 0, 0, TOP_X, TOP_Y, CORNER_R)
        sk_top.isComputeDeferred = False
        prof_top = sk_top.profiles.item(0)

        # --- loft solid body ---
        lin = feats.loftFeatures.createInput(
            adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        lin.loftSections.add(prof_base)
        lin.loftSections.add(prof_top)
        lin.isSolid = True
        loft = feats.loftFeatures.add(lin)
        body = loft.bodies.item(0)
        body.name = "Keycap"

        # --- raised cylinder, join ---
        sk_cyl = comp.sketches.add(plane_top)
        sk_cyl.sketchCurves.sketchCircles.addByCenterRadius(
            p3(0, 0), cm(CYL_DIA / 2.0))
        ein = feats.extrudeFeatures.createInput(
            sk_cyl.profiles.item(0),
            adsk.fusion.FeatureOperations.JoinFeatureOperation)
        ein.setDistanceExtent(False, val(CYL_H))
        feats.extrudeFeatures.add(ein)

        # --- spherical dish cut on cylinder face ---
        a = CYL_DIA / 2.0
        d = DISH_DEPTH
        R = (a * a + d * d) / (2.0 * d)
        top_surface_z = BODY_H + CYL_H
        center_z = top_surface_z - d + R
        tmp = adsk.fusion.TemporaryBRepManager.get()
        sphere = tmp.createSphere(p3(0, 0, center_z), cm(R))
        bf = comp.features.baseFeatures.add()
        bf.startEdit()
        sph_body = comp.bRepBodies.add(sphere, bf)
        sph_body.name = "dish_tool"
        bf.finishEdit()
        tools = adsk.core.ObjectCollection.create()
        tools.add(comp.bRepBodies.itemByName("dish_tool"))
        cin = feats.combineFeatures.createInput(
            comp.bRepBodies.itemByName("Keycap"), tools)
        cin.operation = adsk.fusion.FeatureOperations.CutFeatureOperation
        cin.isKeepToolBodies = False
        feats.combineFeatures.add(cin)

        # --- underside relief pocket (optional) ---
        if RELIEF_DEPTH > 0:
            sk_rel = comp.sketches.add(comp.xYConstructionPlane)
            sk_rel.isComputeDeferred = True
            add_rounded_rect(sk_rel, 0, 0, RELIEF_X, RELIEF_Y, RELIEF_R)
            sk_rel.isComputeDeferred = False
            rin = feats.extrudeFeatures.createInput(
                sk_rel.profiles.item(0),
                adsk.fusion.FeatureOperations.CutFeatureOperation)
            rin.setDistanceExtent(False, val(RELIEF_DEPTH))
            feats.extrudeFeatures.add(rin)

        # --- Choc stem slots, cut up from bottom ---
        sk_stem = comp.sketches.add(comp.xYConstructionPlane)
        sk_stem.isComputeDeferred = True
        add_rounded_rect(sk_stem, +STEM_PITCH / 2.0, 0, STEM_SLOT_W, STEM_SLOT_L, STEM_R)
        add_rounded_rect(sk_stem, -STEM_PITCH / 2.0, 0, STEM_SLOT_W, STEM_SLOT_L, STEM_R)
        sk_stem.isComputeDeferred = False
        slot_profs = adsk.core.ObjectCollection.create()
        for pr in sk_stem.profiles:
            slot_profs.add(pr)
        sin = feats.extrudeFeatures.createInput(
            slot_profs, adsk.fusion.FeatureOperations.CutFeatureOperation)
        sin.setDistanceExtent(False, val(STEM_DEPTH))
        feats.extrudeFeatures.add(sin)

        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        ui.messageBox("Keycap_1u built.\nEdit PARAMETERS and re-run to iterate.")

    except:
        if ui:
            ui.messageBox("Failed:\n{}".format(traceback.format_exc()))
