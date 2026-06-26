# Choc v1 keycap, 1u, Choc-spaced - parametric rebuild (v8)
# KEA-like: vertical skirt (extrude up) -> tapered top (loft) -> SHELL the box ->
# join SOLID raised cylinder -> PARAMETRIC dish (revolve cut, follows the params) ->
# stems from the recessed ceiling, protruding STEM_PROTRUDE below the bottom plane.
#
# LIVE PARAMETERS (Modify > Change Parameters): skirt_h, taper_h, cyl_dia, cyl_h,
#   dish_depth. The dish is now a REVOLVE bound to these, so changing taper_h /
#   cyl_h / cyl_dia / dish_depth keeps the dish attached - no re-run needed for it.
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
SKIRT_H       = 2.5    # vertical skirt height       -> LIVE param "skirt_h"
TAPER_H       = 2.0    # lofted taper offset height  -> LIVE param "taper_h"
CORNER_R      = 1.5    # cap corner radius

CYL_DIA       = 13.0   # raised cylinder diameter    -> LIVE param "cyl_dia"
CYL_H         = 1.5    # raised cylinder height       -> LIVE param "cyl_h"
DISH_DEPTH    = 0.8    # spherical dish depth         -> LIVE param "dish_depth"

WALL          = 1.2    # shell wall thickness (hollow underside; box only)

STEM_W        = 1.2    # stem tower width  (X)  -- Choc nominal
STEM_L        = 3.0    # stem tower length (Y)  -- Choc nominal
STEM_PITCH    = 5.7    # stem center-to-center (X)
STEM_PROTRUDE = 1.4    # how far stems extend BELOW the cap bottom plane
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
    best = None
    best_z = 1e9
    for f in body.faces:
        bb = f.boundingBox
        if abs(bb.maxPoint.z - bb.minPoint.z) < 1e-5:
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

        ensure_param(design, "skirt_h", "{} mm".format(SKIRT_H), "mm", "vertical skirt height")
        ensure_param(design, "taper_h", "{} mm".format(TAPER_H), "mm", "lofted taper offset height (LIVE)")
        ensure_param(design, "cyl_dia", "{} mm".format(CYL_DIA), "mm", "raised cylinder diameter")
        ensure_param(design, "cyl_h", "{} mm".format(CYL_H), "mm", "raised cylinder height")
        ensure_param(design, "dish_depth", "{} mm".format(DISH_DEPTH), "mm", "dish depth")
        # spherical dish radius derived from cyl_dia + dish_depth (kept live)
        ensure_param(design, "dish_r",
                     "(((cyl_dia / 2) * (cyl_dia / 2)) + (dish_depth * dish_depth)) / (2 * dish_depth)",
                     "mm", "derived dish sphere radius")

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

        def plane_expr(expr):
            pin = planes.createInput()
            pin.setByOffset(comp.xYConstructionPlane,
                            adsk.core.ValueInput.createByString(expr))
            return planes.add(pin)

        # --- 1. base profile + vertical skirt extrude ---
        sk_base = comp.sketches.add(comp.xYConstructionPlane)
        sk_base.isComputeDeferred = True
        add_rounded_rect(sk_base, 0, 0, BASE_X, BASE_Y, CORNER_R)
        sk_base.isComputeDeferred = False
        ein = feats.extrudeFeatures.createInput(
            sk_base.profiles.item(0),
            adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        ein.setDistanceExtent(False, adsk.core.ValueInput.createByString("skirt_h"))
        ext = feats.extrudeFeatures.add(ein)
        body = ext.bodies.item(0)
        body.name = "Keycap"

        # --- 2. loft taper from skirt top to smaller top ---
        plane_skirt = plane_expr("skirt_h")
        sk_st = comp.sketches.add(plane_skirt)
        sk_st.isComputeDeferred = True
        add_rounded_rect(sk_st, 0, 0, BASE_X, BASE_Y, CORNER_R)
        sk_st.isComputeDeferred = False

        plane_top = plane_expr("skirt_h + taper_h")
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

        # --- 3. shell the BOX (remove bottom face) -- before the cylinder ---
        cap = comp.bRepBodies.itemByName("Keycap")
        bottom = lowest_horizontal_face(cap)
        faces = adsk.core.ObjectCollection.create()
        faces.add(bottom)
        sh_in = feats.shellFeatures.createInput(faces, False)
        sh_in.insideThickness = val(WALL)
        feats.shellFeatures.add(sh_in)

        # --- 4. raised SOLID cylinder (LIVE: cyl_dia / cyl_h), joined on top ---
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

        # --- 5. PARAMETRIC spherical dish: revolve a semicircle, cut ---
        # numeric current values for the initial sketch geometry
        a0 = CYL_DIA / 2.0
        d0 = DISH_DEPTH
        R0 = (a0 * a0 + d0 * d0) / (2.0 * d0)
        Bz = SKIRT_H + TAPER_H + CYL_H - d0      # deepest dish point z (mm)
        Tz = Bz + 2.0 * R0                       # top of the sphere (mm)
        sk_d = comp.sketches.add(comp.xZConstructionPlane)
        sgn = 1.0 if sk_d.yDirection.z >= 0 else -1.0   # XZ plane Y->Z sign
        B = adsk.core.Point3D.create(0, sgn * cm(Bz), 0)
        T = adsk.core.Point3D.create(0, sgn * cm(Tz), 0)
        Rp = adsk.core.Point3D.create(cm(R0), sgn * cm(Bz + R0), 0)
        ln = sk_d.sketchCurves.sketchLines.addByTwoPoints(B, T)   # diameter on axis
        arc = sk_d.sketchCurves.sketchArcs.addByThreePoints(B, Rp, T)
        # pin the diameter line to the Z axis (u = 0) and revolve about it
        axis_proj = sk_d.project(comp.zConstructionAxis)
        cons = sk_d.geometricConstraints
        if axis_proj.count > 0:
            axisline = axis_proj.item(0)
            cons.addCoincident(ln.startSketchPoint, axisline)
            cons.addCoincident(ln.endSketchPoint, axisline)
            rev_axis = axisline
        else:
            cons.addVertical(ln)
            rev_axis = ln
        dims = sk_d.sketchDimensions
        rd = dims.addRadialDimension(arc, Rp)
        rd.parameter.expression = "dish_r"
        hd = dims.addDistanceDimension(
            sk_d.originPoint, ln.startSketchPoint,
            adsk.fusion.DimensionOrientations.VerticalDimensionOrientation,
            adsk.core.Point3D.create(cm(2.0), sgn * cm(Bz), 0))
        hd.parameter.expression = "skirt_h + taper_h + cyl_h - dish_depth"
        prof_d = sk_d.profiles.item(0)
        rin = feats.revolveFeatures.createInput(
            prof_d, rev_axis, adsk.fusion.FeatureOperations.CutFeatureOperation)
        rin.setAngleExtent(False, adsk.core.ValueInput.createByString("360 deg"))
        rin.participantBodies = [comp.bRepBodies.itemByName("Keycap")]
        feats.revolveFeatures.add(rin)

        # --- 6. stem towers: start STEM_PROTRUDE below the bottom plane,
        #        extrude up to the recessed ceiling, then join ---
        cap = comp.bRepBodies.itemByName("Keycap")
        plane_stem = plane_at(-STEM_PROTRUDE)
        sk_stem = comp.sketches.add(plane_stem)
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
            st_in.setDistanceExtent(False, val(SKIRT_H + TAPER_H - WALL + STEM_PROTRUDE))
        st_ext = feats.extrudeFeatures.add(st_in)
        stem_tools = adsk.core.ObjectCollection.create()
        for b in st_ext.bodies:
            stem_tools.add(b)
        jin = feats.combineFeatures.createInput(
            comp.bRepBodies.itemByName("Keycap"), stem_tools)
        jin.operation = adsk.fusion.FeatureOperations.JoinFeatureOperation
        jin.isKeepToolBodies = False
        feats.combineFeatures.add(jin)

        ui.messageBox("Keycap_1u (v8) built.\n"
                      "Dish is now a parametric revolve - follows skirt_h/taper_h/cyl_h/dish_depth.\n"
                      "All heights live in Change Parameters.")

    except:
        if ui:
            ui.messageBox("Failed:\n{}".format(traceback.format_exc()))
