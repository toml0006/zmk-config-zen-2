# Choc/MX keycap - parametric rebuild (v10)
# Vertical skirt -> tapered loft -> shell box -> solid cylinder -> dish/bump ->
# stems from the recessed ceiling. Configurable: U width, spacing, stem type,
# top style.
#
# CHOICE PARAMETERS (script constants - set then RE-RUN; not live):
#   U          key width in units (1, 1.25, 1.5, 2 ...). Depth always 1u.
#   SPACING    "choc" (18x17) or "mx" (19.05 x 19.05)
#   STEM_TYPE  "choc" (twin towers) or "mx" (+ cross mount)
#   TOP_STYLE  "dish" (concave) or "bump" (convex dome)
#
# LIVE PARAMETERS (Modify > Change Parameters): skirt_h, taper_h, cyl_dia, cyl_h,
#   dish_depth (dish depth / bump height). Body + dish/bump track these live.
#
# HOW TO RUN: Utilities > ADD-INS > Scripts and Add-Ins (Shift+S) > Scripts >
#   point at this folder > Run. Re-run after editing the block below.
#
# Units in this file are MILLIMETERS (converted to Fusion's internal cm on use).

import adsk.core, adsk.fusion, traceback, math

# ============================ CHOICES ============================
U          = 1.0       # key width in units
SPACING    = "choc"    # "choc" | "mx"
STEM_TYPE  = "choc"    # "choc" | "mx"
TOP_STYLE  = "dish"    # "dish" | "bump"

# ============================ PARAMETERS (mm) ============================
TAPER_INSET_X = 2.0    # how much smaller the top is than the base, in X (total)
TAPER_INSET_Y = 1.9    # ... in Y
SKIRT_H       = 2.5    # vertical skirt height       -> LIVE "skirt_h"
TAPER_H       = 2.0    # lofted taper offset height   -> LIVE "taper_h"
CORNER_R      = 1.5    # cap corner radius

CYL_DIA       = 13.0   # raised cylinder diameter     -> LIVE "cyl_dia"
CYL_H         = 1.5    # raised cylinder height        -> LIVE "cyl_h"
DISH_DEPTH    = 0.8    # dish depth OR bump height     -> LIVE "dish_depth"

WALL          = 1.2    # shell wall thickness (box only)

# Choc stem (twin solid towers)
CHOC_STEM_W   = 1.2
CHOC_STEM_L   = 3.0
CHOC_PITCH    = 5.7
# MX stem (+ cross in a cylindrical boss)
MX_STEM_DIA   = 5.5
MX_CROSS_LEN  = 4.1
MX_CROSS_W1   = 1.17   # vertical arm width
MX_CROSS_W2   = 1.31   # horizontal arm width
MX_CROSS_DEPTH= 3.9    # depth of the + cut up from the stem bottom
# common stem
STEM_PROTRUDE = 1.4    # how far the stem extends BELOW the cap bottom plane
STEM_R        = 0.3    # choc tower corner radius

COMP_NAME     = "Keycap"
# =========================================================================

# spacing table: pitch_x, pitch_y, cap gap
_SPACING = {"choc": (18.0, 17.0, 0.5), "mx": (19.05, 19.05, 1.05)}
PITCH_X, PITCH_Y, GAP = _SPACING[SPACING]
BASE_X = U * PITCH_X - GAP
BASE_Y = 1.0 * PITCH_Y - GAP
TOP_X = BASE_X - TAPER_INSET_X
TOP_Y = BASE_Y - TAPER_INSET_Y


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
    best, best_z = None, 1e9
    for f in body.faces:
        bb = f.boundingBox
        if abs(bb.maxPoint.z - bb.minPoint.z) < 1e-5 and bb.minPoint.z < best_z:
            best_z, best = bb.minPoint.z, f
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
        ensure_param(design, "taper_h", "{} mm".format(TAPER_H), "mm", "lofted taper offset height")
        ensure_param(design, "cyl_dia", "{} mm".format(CYL_DIA), "mm", "raised cylinder diameter")
        ensure_param(design, "cyl_h", "{} mm".format(CYL_H), "mm", "raised cylinder height")
        ensure_param(design, "dish_depth", "{} mm".format(DISH_DEPTH), "mm", "dish depth / bump height")
        ensure_param(design, "dish_r",
                     "(((cyl_dia / 2) * (cyl_dia / 2)) + (dish_depth * dish_depth)) / (2 * dish_depth)",
                     "mm", "derived dish/bump sphere radius")

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

        def cap_body():
            return comp.bRepBodies.itemByName("Keycap")

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
        ext.bodies.item(0).name = "Keycap"

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

        # --- 3. shell the BOX (remove bottom face) ---
        bottom = lowest_horizontal_face(cap_body())
        faces = adsk.core.ObjectCollection.create()
        faces.add(bottom)
        sh_in = feats.shellFeatures.createInput(faces, False)
        sh_in.insideThickness = val(WALL)
        feats.shellFeatures.add(sh_in)

        # --- 4. raised SOLID cylinder (LIVE cyl_dia / cyl_h) ---
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

        # --- 5. dish (concave Cut) or bump (convex Join) - parametric revolve ---
        a0 = CYL_DIA / 2.0
        d0 = DISH_DEPTH
        R0 = (a0 * a0 + d0 * d0) / (2.0 * d0)
        if TOP_STYLE == "bump":
            cz = SKIRT_H + TAPER_H + CYL_H + d0 - R0
            cz_expr = "skirt_h + taper_h + cyl_h + dish_depth - dish_r"
            top_op = adsk.fusion.FeatureOperations.JoinFeatureOperation
        else:
            cz = SKIRT_H + TAPER_H + CYL_H - d0 + R0
            cz_expr = "skirt_h + taper_h + cyl_h - dish_depth + dish_r"
            top_op = adsk.fusion.FeatureOperations.CutFeatureOperation
        sk_d = comp.sketches.add(comp.xZConstructionPlane)
        sgn = 1.0 if sk_d.yDirection.z >= 0 else -1.0
        Cv = sgn * cm(cz)
        C = adsk.core.Point3D.create(0, Cv, 0)
        S = adsk.core.Point3D.create(0, Cv - cm(R0), 0)
        arc = sk_d.sketchCurves.sketchArcs.addByCenterStartSweep(C, S, math.pi)
        ln = sk_d.sketchCurves.sketchLines.addByTwoPoints(
            arc.startSketchPoint, arc.endSketchPoint)
        cons = sk_d.geometricConstraints
        axis_proj = sk_d.project(comp.zConstructionAxis)
        if axis_proj.count > 0:
            axisline = axis_proj.item(0)
            cons.addCoincident(arc.centerSketchPoint, axisline)
            cons.addCoincident(arc.startSketchPoint, axisline)
            cons.addCoincident(arc.endSketchPoint, axisline)
            rev_axis = axisline
        else:
            cons.addVertical(ln)
            rev_axis = ln
        dims = sk_d.sketchDimensions
        rd = dims.addRadialDimension(arc, adsk.core.Point3D.create(cm(R0 / 2.0), Cv, 0))
        rd.parameter.expression = "dish_r"
        hd = dims.addDistanceDimension(
            sk_d.originPoint, arc.centerSketchPoint,
            adsk.fusion.DimensionOrientations.VerticalDimensionOrientation,
            adsk.core.Point3D.create(cm(2.0), Cv, 0))
        hd.parameter.expression = cz_expr
        rin = feats.revolveFeatures.createInput(sk_d.profiles.item(0), rev_axis, top_op)
        rin.setAngleExtent(False, adsk.core.ValueInput.createByString("360 deg"))
        rin.participantBodies = [cap_body()]
        feats.revolveFeatures.add(rin)

        # --- 6. stems grown from the recessed ceiling ---
        fallback = val(SKIRT_H + TAPER_H - WALL + STEM_PROTRUDE)

        def grow_join(sketch):
            profs = adsk.core.ObjectCollection.create()
            for pr in sketch.profiles:
                profs.add(pr)
            gi = feats.extrudeFeatures.createInput(
                profs, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            try:
                td = adsk.fusion.ToEntityExtentDefinition.create(cap_body(), False)
                gi.setOneSideExtent(td, adsk.fusion.ExtentDirections.PositiveExtentDirection)
            except:
                gi.setDistanceExtent(False, fallback)
            ge = feats.extrudeFeatures.add(gi)
            tools = adsk.core.ObjectCollection.create()
            for b in ge.bodies:
                tools.add(b)
            ji = feats.combineFeatures.createInput(cap_body(), tools)
            ji.operation = adsk.fusion.FeatureOperations.JoinFeatureOperation
            ji.isKeepToolBodies = False
            feats.combineFeatures.add(ji)

        plane_stem = plane_at(-STEM_PROTRUDE)

        if STEM_TYPE == "mx":
            # central cylindrical boss grown to ceiling
            sk_boss = comp.sketches.add(plane_stem)
            sk_boss.sketchCurves.sketchCircles.addByCenterRadius(p3(0, 0), cm(MX_STEM_DIA / 2.0))
            grow_join(sk_boss)
            # + cross cut from the stem bottom upward
            sk_x = comp.sketches.add(plane_stem)
            sk_x.isComputeDeferred = True
            add_rounded_rect(sk_x, 0, 0, MX_CROSS_W1, MX_CROSS_LEN, 0)   # vertical arm
            add_rounded_rect(sk_x, 0, 0, MX_CROSS_LEN, MX_CROSS_W2, 0)   # horizontal arm
            sk_x.isComputeDeferred = False
            xprofs = adsk.core.ObjectCollection.create()
            for pr in sk_x.profiles:
                xprofs.add(pr)
            xi = feats.extrudeFeatures.createInput(
                xprofs, adsk.fusion.FeatureOperations.CutFeatureOperation)
            xi.setDistanceExtent(False, val(MX_CROSS_DEPTH))
            feats.extrudeFeatures.add(xi)
        else:
            # choc: two solid towers
            sk_stem = comp.sketches.add(plane_stem)
            sk_stem.isComputeDeferred = True
            add_rounded_rect(sk_stem, +CHOC_PITCH / 2.0, 0, CHOC_STEM_W, CHOC_STEM_L, STEM_R)
            add_rounded_rect(sk_stem, -CHOC_PITCH / 2.0, 0, CHOC_STEM_W, CHOC_STEM_L, STEM_R)
            sk_stem.isComputeDeferred = False
            grow_join(sk_stem)

        ui.messageBox(
            "Keycap built (v10).\n"
            "U={}  spacing={}  stem={}  top={}\n"
            "Heights/dia/dish live in Change Parameters; re-run to change the choices.".format(
                U, SPACING, STEM_TYPE, TOP_STYLE))

    except:
        if ui:
            ui.messageBox("Failed:\n{}".format(traceback.format_exc()))
