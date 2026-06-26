# Choc v1 keycap, 1u, Choc-spaced - parametric rebuild (v4)
# KEA-like: vertical skirt (extrude up) -> tapered top (loft) -> raised dished cylinder.
# SHELLED underside (hollow). Two solid Choc stem towers grown from the recessed
# inner ceiling down to the bottom opening (5.7mm pitch).
#
# LIVE PARAMETERS: cyl_dia, cyl_h, dish_depth are Fusion User Parameters
#   (Modify > Change Parameters). cyl_dia & cyl_h drive the cylinder live.
#   The dish is a static boolean - re-run the script to refresh it after changing
#   cyl size.
#
# HOW TO RUN: Utilities > ADD-INS > Scripts and Add-Ins (Shift+S) > Scripts >
#   point at this folder > Run. Re-run after editing the block below.
#
# Units in this file are MILLIMETERS (converted to Fusion's internal cm on use).

import adsk.core, adsk.fusion, traceback, math

# ============================ PARAMETERS (mm) ============================
BASE_X        = 17.5   # bottom footprint X (Choc-spaced 1u)
BASE_Y        = 16.5   # bottom footprint Y
TOP_X         = 15.5   # top footprint X (taper target)
TOP_Y         = 14.6   # top footprint Y
SKIRT_H       = 2.5    # vertical skirt height (straight extrude up)
TAPER_H       = 2.0    # loft height above skirt (taper to top)
CORNER_R      = 1.5    # cap corner radius

CYL_DIA       = 13.0   # raised cylinder diameter  -> LIVE user param "cyl_dia"
CYL_H         = 1.5    # raised cylinder height     -> LIVE user param "cyl_h"
DISH_DEPTH    = 0.8    # spherical dish depth        -> user param "dish_depth"

WALL          = 1.2    # shell wall thickness (hollow underside)

STEM_W        = 1.2    # stem tower width  (X)  -- Choc nominal
STEM_L        = 3.0    # stem tower length (Y)  -- Choc nominal
STEM_PITCH    = 5.7    # stem center-to-center (X)
STEM_R        = 0.3    # stem corner radius

COMP_NAME     = "Keycap_1u"
# =========================================================================


def cm(mm):
    return mm * 0.1


def val(mm):
    return adsk.core.ValueInput.createByReal(cm(mm))


def p3(x_mm, y_mm, z_mm=0.0):
    return adsk.core.Point3D.create(cm(x_mm), cm(y_mm), cm(z_mm))


def add_rounded_rect(sketch, cx, cy, w, h, r):
    lines = sketch.sketchCurves.sketchLines
    arcs = sketch.sketchCurves.sketchArcs
    r = max(0.0, min(r, (min(w, h) / 2.0) - 1e-4))
    hw, hh = w / 2.0, h / 2.0
    if r <= 0.0:
        lines.addTwoPointRectangle(p3(cx - hw, cy - hh), p3(cx + hw, cy + hh))
        return
    q = math.pi / 2.0
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


def ensure_param(design, name, expr, unit, comment):
    p = design.userParameters.itemByName(name)
    if p:
        p.expression = expr
        return p
    return design.userParameters.add(
        name, adsk.core.ValueInput.createByString(expr), unit, comment)


def lowest_horizontal_face(body):
    """Return the lowest (min-z) horizontal planar face = the bottom face."""
    best = None
    best_z = 1e9
    for f in body.faces:
        bb = f.boundingBox
        if abs(bb.maxPoint.z - bb.minPoint.z) < 1e-5:   # horizontal
            if bb.minPoint.z < best_z:
                best_z = bb.minPoint.z
                best = f
    return best


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        design = adsk.fusion.Design.cast(app.activeProduct)
        if not design:
            ui.messageBox("Open a Fusion Design first.")
            return
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        root = design.rootComponent

        ensure_param(design, "cyl_dia", "{} mm".format(CYL_DIA), "mm", "raised cylinder diameter")
        ensure_param(design, "cyl_h", "{} mm".format(CYL_H), "mm", "raised cylinder height")
        ensure_param(design, "dish_depth", "{} mm".format(DISH_DEPTH), "mm", "dish depth (re-run to refresh)")

        for occ in list(root.occurrences):
            if occ.component.name == COMP_NAME:
                occ.deleteMe()

        occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        comp = occ.component
        comp.name = COMP_NAME
        feats = comp.features
        planes = comp.constructionPlanes

        def plane_at(z_mm):
            pin = planes.createInput()
            pin.setByOffset(comp.xYConstructionPlane, val(z_mm))
            return planes.add(pin)

        # --- 1. base profile + vertical skirt extrude ---
        sk_base = comp.sketches.add(comp.xYConstructionPlane)
        sk_base.isComputeDeferred = True
        add_rounded_rect(sk_base, 0, 0, BASE_X, BASE_Y, CORNER_R)
        sk_base.isComputeDeferred = False
        ein = feats.extrudeFeatures.createInput(
            sk_base.profiles.item(0),
            adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        ein.setDistanceExtent(False, val(SKIRT_H))
        ext = feats.extrudeFeatures.add(ein)
        body = ext.bodies.item(0)
        body.name = "Keycap"

        # --- 2. loft taper from skirt top to smaller top ---
        plane_skirt = plane_at(SKIRT_H)
        sk_st = comp.sketches.add(plane_skirt)
        sk_st.isComputeDeferred = True
        add_rounded_rect(sk_st, 0, 0, BASE_X, BASE_Y, CORNER_R)
        sk_st.isComputeDeferred = False

        plane_top = plane_at(SKIRT_H + TAPER_H)
        sk_top = comp.sketches.add(plane_top)
        sk_top.isComputeDeferred = True
        add_rounded_rect(sk_top, 0, 0, TOP_X, TOP_Y, CORNER_R)
        sk_top.isComputeDeferred = False

        lin = feats.loftFeatures.createInput(
            adsk.fusion.FeatureOperations.JoinFeatureOperation)
        lin.loftSections.add(sk_st.profiles.item(0))
        lin.loftSections.add(sk_top.profiles.item(0))
        lin.isSolid = True
        feats.loftFeatures.add(lin)

        # --- 3. raised cylinder (LIVE: driven by cyl_dia / cyl_h) ---
        sk_cyl = comp.sketches.add(plane_top)
        circ = sk_cyl.sketchCurves.sketchCircles.addByCenterRadius(
            p3(0, 0), cm(CYL_DIA / 2.0))
        try:
            ddim = sk_cyl.sketchDimensions.addDiameterDimension(
                circ, p3(CYL_DIA / 2.0, 0, 0))
            ddim.parameter.expression = "cyl_dia"
        except:
            pass
        cin = feats.extrudeFeatures.createInput(
            sk_cyl.profiles.item(0),
            adsk.fusion.FeatureOperations.JoinFeatureOperation)
        cin.setDistanceExtent(False, adsk.core.ValueInput.createByString("cyl_h"))
        feats.extrudeFeatures.add(cin)

        # --- 4. spherical dish cut (static; uses current param values) ---
        a = design.userParameters.itemByName("cyl_dia").value / 2.0   # cm
        d = design.userParameters.itemByName("dish_depth").value      # cm
        ch = design.userParameters.itemByName("cyl_h").value          # cm
        R = (a * a + d * d) / (2.0 * d)
        top_z = cm(SKIRT_H + TAPER_H) + ch
        center_z = top_z - d + R
        tmp = adsk.fusion.TemporaryBRepManager.get()
        sphere = tmp.createSphere(adsk.core.Point3D.create(0, 0, center_z), R)
        bf = comp.features.baseFeatures.add()
        bf.startEdit()
        sph = comp.bRepBodies.add(sphere, bf)
        sph.name = "dish_tool"
        bf.finishEdit()
        tools = adsk.core.ObjectCollection.create()
        tools.add(comp.bRepBodies.itemByName("dish_tool"))
        combin = feats.combineFeatures.createInput(
            comp.bRepBodies.itemByName("Keycap"), tools)
        combin.operation = adsk.fusion.FeatureOperations.CutFeatureOperation
        combin.isKeepToolBodies = False
        feats.combineFeatures.add(combin)

        # --- 5. shell the underside (remove bottom face) ---
        cap = comp.bRepBodies.itemByName("Keycap")
        bottom = lowest_horizontal_face(cap)
        faces = adsk.core.ObjectCollection.create()
        faces.add(bottom)
        sh_in = feats.shellFeatures.createInput(faces, False)
        sh_in.insideThickness = val(WALL)
        feats.shellFeatures.add(sh_in)

        # --- 6. stem towers grown from the recessed ceiling, joined ---
        cap = comp.bRepBodies.itemByName("Keycap")
        sk_stem = comp.sketches.add(comp.xYConstructionPlane)
        sk_stem.isComputeDeferred = True
        add_rounded_rect(sk_stem, +STEM_PITCH / 2.0, 0, STEM_W, STEM_L, STEM_R)
        add_rounded_rect(sk_stem, -STEM_PITCH / 2.0, 0, STEM_W, STEM_L, STEM_R)
        sk_stem.isComputeDeferred = False
        stem_profs = adsk.core.ObjectCollection.create()
        for pr in sk_stem.profiles:
            stem_profs.add(pr)
        st_in = feats.extrudeFeatures.createInput(
            stem_profs, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        try:
            to_def = adsk.fusion.ToEntityExtentDefinition.create(cap, False)
            st_in.setOneSideExtent(
                to_def, adsk.fusion.ExtentDirections.PositiveExtentDirection)
        except:
            st_in.setDistanceExtent(False, val(SKIRT_H + TAPER_H + 1.0))
        st_ext = feats.extrudeFeatures.add(st_in)
        stem_tools = adsk.core.ObjectCollection.create()
        for b in st_ext.bodies:
            stem_tools.add(b)
        jin = feats.combineFeatures.createInput(
            comp.bRepBodies.itemByName("Keycap"), stem_tools)
        jin.operation = adsk.fusion.FeatureOperations.JoinFeatureOperation
        jin.isKeepToolBodies = False
        feats.combineFeatures.add(jin)

        ui.messageBox("Keycap_1u (v4) built.\n"
                      "Shelled underside + stems from the recessed ceiling.\n"
                      "cyl_dia / cyl_h live in Change Parameters; re-run to refresh dish.")

    except:
        if ui:
            ui.messageBox("Failed:\n{}".format(traceback.format_exc()))
