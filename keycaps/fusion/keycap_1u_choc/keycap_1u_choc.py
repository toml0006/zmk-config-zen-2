# Choc/MX keycap generator - parametric, dialog-driven (v12)
# Vertical skirt -> tapered loft -> shell box -> (inner-wall draft) -> solid cylinder
# -> dish/bump -> stems -> edge chamfers. Builds in the ROOT component (Part docs ok).
#
# Dialog: U, Spacing, Stem, Top, skirt_h, taper_h, cyl_dia, cyl_h, dish_depth, wall,
#   draft_deg (inner-wall taper), and chamfers: top / bottom / cyl-rim / skirt edges.
# All numeric values become live User Parameters. Re-running clears the timeline.
#
# HOW TO RUN: Utilities > ADD-INS > Scripts and Add-Ins (Shift+S) > Scripts >
#   point at this folder > Run.

import adsk.core, adsk.fusion, traceback, math

TAPER_INSET_X = 2.0
TAPER_INSET_Y = 1.9
CORNER_R      = 1.5
SQUIRCLE_N    = 4.0    # squircle exponent for the top loft profile (higher=squarer)
CHOC_STEM_W   = 1.2
CHOC_STEM_L   = 3.0
CHOC_PITCH    = 5.7
MX_STEM_DIA   = 5.5
MX_CROSS_LEN  = 4.1
MX_CROSS_W1   = 1.17
MX_CROSS_W2   = 1.31
MX_CROSS_DEPTH= 3.9
STEM_PROTRUDE = 1.4
STEM_R        = 0.3

_SPACING = {"choc": (18.0, 17.0, 0.5), "mx": (19.05, 19.05, 1.05)}
_handlers = []


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


def add_squircle(sketch, cx, cy, w, h, n=4.0, npts=72):
    a = w / 2.0
    b = h / 2.0
    pts = adsk.core.ObjectCollection.create()
    for k in range(npts):
        t = 2.0 * math.pi * k / npts
        ct = math.cos(t)
        st = math.sin(t)
        x = a * (abs(ct) ** (2.0 / n)) * (1.0 if ct >= 0 else -1.0)
        y = b * (abs(st) ** (2.0 / n)) * (1.0 if st >= 0 else -1.0)
        pts.add(p3(cx + x, cy + y))
    spl = sketch.sketchCurves.sketchFittedSplines.add(pts)
    spl.isClosed = True
    return spl


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


def clear_design(design):
    tl = design.timeline
    for i in range(tl.count - 1, -1, -1):
        try:
            tl.item(i).deleteMe()
        except:
            pass
    for b in list(design.rootComponent.bRepBodies):
        try:
            b.deleteMe()
        except:
            pass


def edge_zspan(e):
    bb = e.boundingBox
    return (bb.minPoint.z + bb.maxPoint.z) / 2.0, (bb.maxPoint.z - bb.minPoint.z)


def edge_radius(e):
    bb = e.boundingBox
    cx = (bb.minPoint.x + bb.maxPoint.x) / 2.0
    cy = (bb.minPoint.y + bb.maxPoint.y) / 2.0
    rmid = math.hypot(cx, cy)
    rext = max(bb.maxPoint.x - bb.minPoint.x, bb.maxPoint.y - bb.minPoint.y) / 2.0
    return max(rmid, rext)


def build(design, v):
    design.designType = adsk.fusion.DesignTypes.ParametricDesignType
    clear_design(design)

    ensure_param(design, "skirt_h", "{} mm".format(v["skirt_h"]), "mm", "vertical skirt height")
    ensure_param(design, "taper_h", "{} mm".format(v["taper_h"]), "mm", "lofted taper offset height")
    ensure_param(design, "cyl_dia", "{} mm".format(v["cyl_dia"]), "mm", "raised cylinder diameter")
    ensure_param(design, "cyl_h", "{} mm".format(v["cyl_h"]), "mm", "raised cylinder height")
    ensure_param(design, "dish_depth", "{} mm".format(v["dish_depth"]), "mm", "dish depth / bump height")
    ensure_param(design, "dish_r",
                 "(((cyl_dia / 2) * (cyl_dia / 2)) + (dish_depth * dish_depth)) / (2 * dish_depth)",
                 "mm", "derived dish/bump sphere radius")
    ensure_param(design, "draft_deg", "{} deg".format(v["draft_deg"]), "deg", "inner wall draft angle")
    ensure_param(design, "chamfer_top", "{} mm".format(v["chamfer_top"]), "mm", "top perimeter chamfer")
    ensure_param(design, "chamfer_bottom", "{} mm".format(v["chamfer_bottom"]), "mm", "bottom edge chamfer")
    ensure_param(design, "chamfer_cyl", "{} mm".format(v["chamfer_cyl"]), "mm", "cylinder rim chamfer")
    ensure_param(design, "chamfer_skirt", "{} mm".format(v["chamfer_skirt"]), "mm", "skirt/taper edge chamfer")

    px, py, gap = _SPACING[v["spacing"]]
    BASE_X = v["U"] * px - gap
    BASE_Y = 1.0 * py - gap
    TOP_X = BASE_X - TAPER_INSET_X
    TOP_Y = BASE_Y - TAPER_INSET_Y
    SKIRT_H = v["skirt_h"]; TAPER_H = v["taper_h"]
    CYL_DIA = v["cyl_dia"]; CYL_H = v["cyl_h"]; DISH_DEPTH = v["dish_depth"]; WALL = v["wall"]

    comp = design.rootComponent
    feats = comp.features
    planes = comp.constructionPlanes

    def plane_at(z_mm):
        pin = planes.createInput()
        pin.setByOffset(comp.xYConstructionPlane, val(z_mm))
        return planes.add(pin)

    def plane_expr(expr):
        pin = planes.createInput()
        pin.setByOffset(comp.xYConstructionPlane, adsk.core.ValueInput.createByString(expr))
        return planes.add(pin)

    def cap_body():
        return comp.bRepBodies.itemByName("Keycap")

    # 1. base + vertical skirt
    sk_base = comp.sketches.add(comp.xYConstructionPlane)
    sk_base.isComputeDeferred = True
    add_rounded_rect(sk_base, 0, 0, BASE_X, BASE_Y, CORNER_R)
    sk_base.isComputeDeferred = False
    ein = feats.extrudeFeatures.createInput(
        sk_base.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    ein.setDistanceExtent(False, adsk.core.ValueInput.createByString("skirt_h"))
    feats.extrudeFeatures.add(ein).bodies.item(0).name = "Keycap"

    # 2. loft taper
    plane_skirt = plane_expr("skirt_h")
    sk_st = comp.sketches.add(plane_skirt)
    sk_st.isComputeDeferred = True
    add_rounded_rect(sk_st, 0, 0, BASE_X, BASE_Y, CORNER_R)
    sk_st.isComputeDeferred = False
    plane_top = plane_expr("skirt_h + taper_h")
    sk_top = comp.sketches.add(plane_top)
    sk_top.isComputeDeferred = True
    add_squircle(sk_top, 0, 0, TOP_X, TOP_Y, SQUIRCLE_N)
    sk_top.isComputeDeferred = False
    lin = feats.loftFeatures.createInput(adsk.fusion.FeatureOperations.JoinFeatureOperation)
    lin.loftSections.add(sk_st.profiles.item(0))
    lin.loftSections.add(sk_top.profiles.item(0))
    lin.isSolid = True
    feats.loftFeatures.add(lin)

    # 3. shell box
    faces = adsk.core.ObjectCollection.create()
    faces.add(lowest_horizontal_face(cap_body()))
    sh_in = feats.shellFeatures.createInput(faces, False)
    sh_in.insideThickness = val(WALL)
    feats.shellFeatures.add(sh_in)

    # 3b. inner-wall draft (taper the cavity walls inward going up)
    if v["draft_deg"] > 0:
        try:
            inner = adsk.core.ObjectCollection.create()
            for f in cap_body().faces:
                g = f.geometry
                if isinstance(g, adsk.core.Plane) and abs(g.normal.z) < 0.05:
                    pt = f.pointOnFace
                    if g.normal.x * (-pt.x) + g.normal.y * (-pt.y) > 0:   # faces inward
                        inner.add(f)
            if inner.count > 0:
                dfeats = feats.draftFeatures
                ang = adsk.core.ValueInput.createByString("draft_deg")
                try:
                    di = dfeats.createInput(inner, comp.xYConstructionPlane, ang, False)
                except:
                    di = dfeats.createInput(inner, comp.xYConstructionPlane, False)
                    di.setSingleSide(ang) if hasattr(di, "setSingleSide") else None
                dfeats.add(di)
        except:
            pass

    # 4. solid cylinder
    sk_cyl = comp.sketches.add(plane_top)
    circ = sk_cyl.sketchCurves.sketchCircles.addByCenterRadius(p3(0, 0), cm(CYL_DIA / 2.0))
    try:
        sk_cyl.sketchDimensions.addDiameterDimension(
            circ, p3(CYL_DIA / 2.0, 0, 0)).parameter.expression = "cyl_dia"
    except:
        pass
    cin = feats.extrudeFeatures.createInput(
        sk_cyl.profiles.item(0), adsk.fusion.FeatureOperations.JoinFeatureOperation)
    cin.setDistanceExtent(False, adsk.core.ValueInput.createByString("cyl_h"))
    feats.extrudeFeatures.add(cin)

    # 5. dish or bump (parametric revolve)
    a0 = CYL_DIA / 2.0; d0 = DISH_DEPTH
    R0 = (a0 * a0 + d0 * d0) / (2.0 * d0)
    if v["top"] == "bump":
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
    arc = sk_d.sketchCurves.sketchArcs.addByCenterStartSweep(
        adsk.core.Point3D.create(0, Cv, 0),
        adsk.core.Point3D.create(0, Cv - cm(R0), 0), math.pi)
    ln = sk_d.sketchCurves.sketchLines.addByTwoPoints(arc.startSketchPoint, arc.endSketchPoint)
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
    dims.addRadialDimension(arc, adsk.core.Point3D.create(cm(R0 / 2.0), Cv, 0)).parameter.expression = "dish_r"
    dims.addDistanceDimension(
        sk_d.originPoint, arc.centerSketchPoint,
        adsk.fusion.DimensionOrientations.VerticalDimensionOrientation,
        adsk.core.Point3D.create(cm(2.0), Cv, 0)).parameter.expression = cz_expr
    rin = feats.revolveFeatures.createInput(sk_d.profiles.item(0), rev_axis, top_op)
    rin.setAngleExtent(False, adsk.core.ValueInput.createByString("360 deg"))
    rin.participantBodies = [cap_body()]
    feats.revolveFeatures.add(rin)

    # 6. stems
    fallback = val(SKIRT_H + TAPER_H - WALL + STEM_PROTRUDE)
    plane_stem = plane_at(-STEM_PROTRUDE)

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

    if v["stem"] == "mx":
        sk_boss = comp.sketches.add(plane_stem)
        sk_boss.sketchCurves.sketchCircles.addByCenterRadius(p3(0, 0), cm(MX_STEM_DIA / 2.0))
        grow_join(sk_boss)
        sk_x = comp.sketches.add(plane_stem)
        sk_x.isComputeDeferred = True
        add_rounded_rect(sk_x, 0, 0, MX_CROSS_W1, MX_CROSS_LEN, 0)
        add_rounded_rect(sk_x, 0, 0, MX_CROSS_LEN, MX_CROSS_W2, 0)
        sk_x.isComputeDeferred = False
        xprofs = adsk.core.ObjectCollection.create()
        for pr in sk_x.profiles:
            xprofs.add(pr)
        xi = feats.extrudeFeatures.createInput(
            xprofs, adsk.fusion.FeatureOperations.CutFeatureOperation)
        xi.setDistanceExtent(False, val(MX_CROSS_DEPTH))
        feats.extrudeFeatures.add(xi)
    else:
        sk_stem = comp.sketches.add(plane_stem)
        sk_stem.isComputeDeferred = True
        add_rounded_rect(sk_stem, +CHOC_PITCH / 2.0, 0, CHOC_STEM_W, CHOC_STEM_L, STEM_R)
        add_rounded_rect(sk_stem, -CHOC_PITCH / 2.0, 0, CHOC_STEM_W, CHOC_STEM_L, STEM_R)
        sk_stem.isComputeDeferred = False
        grow_join(sk_stem)

    # 7. edge chamfers (heuristic Z-level + radial-band selection)
    ztol = cm(0.10)
    z_bottom = cm(0.0)
    z_skirt = cm(SKIRT_H)
    z_top = cm(SKIRT_H + TAPER_H)
    z_cyl = cm(SKIRT_H + TAPER_H + CYL_H)
    r_outer = cm(min(BASE_X, BASE_Y) / 2.0 - 0.6)
    r_topsep = cm((CYL_DIA / 2.0 + min(TOP_X, TOP_Y) / 2.0) / 2.0)
    r_cyl_lo = cm(CYL_DIA / 2.0 - 1.0)
    r_cyl_hi = cm(CYL_DIA / 2.0 + 1.0)
    cfeats = feats.chamferFeatures

    def horiz(e):
        _, dz = edge_zspan(e)
        return dz < cm(0.05)

    def chamfer(pred, param_name, dist_mm):
        if dist_mm <= 0:
            return
        col = adsk.core.ObjectCollection.create()
        for e in cap_body().edges:
            try:
                if pred(e):
                    col.add(e)
            except:
                pass
        if col.count == 0:
            return
        try:
            ci = cfeats.createInput2()
            ci.chamferEdgeSets.addEqualDistanceChamferEdgeSet(
                col, adsk.core.ValueInput.createByString(param_name), True)
            cfeats.add(ci)
        except:
            try:
                ci = cfeats.createInput(col, True)
                ci.setToEqualDistance(val(dist_mm))
                cfeats.add(ci)
            except:
                pass

    chamfer(lambda e: horiz(e) and abs(edge_zspan(e)[0] - z_bottom) < ztol and edge_radius(e) > r_outer,
            "chamfer_bottom", v["chamfer_bottom"])
    chamfer(lambda e: horiz(e) and abs(edge_zspan(e)[0] - z_skirt) < ztol and edge_radius(e) > r_outer,
            "chamfer_skirt", v["chamfer_skirt"])
    chamfer(lambda e: horiz(e) and abs(edge_zspan(e)[0] - z_top) < ztol and edge_radius(e) > r_topsep,
            "chamfer_top", v["chamfer_top"])
    chamfer(lambda e: horiz(e) and abs(edge_zspan(e)[0] - z_cyl) < ztol and r_cyl_lo < edge_radius(e) < r_cyl_hi,
            "chamfer_cyl", v["chamfer_cyl"])


def read_inputs(inputs):
    return {
        "U": inputs.itemById("u").value,
        "spacing": inputs.itemById("spacing").selectedItem.name,
        "stem": inputs.itemById("stem").selectedItem.name,
        "top": inputs.itemById("top").selectedItem.name,
        "skirt_h": inputs.itemById("skirt_h").value * 10.0,
        "taper_h": inputs.itemById("taper_h").value * 10.0,
        "cyl_dia": inputs.itemById("cyl_dia").value * 10.0,
        "cyl_h": inputs.itemById("cyl_h").value * 10.0,
        "dish_depth": inputs.itemById("dish_depth").value * 10.0,
        "wall": inputs.itemById("wall").value * 10.0,
        "draft_deg": math.degrees(inputs.itemById("draft_deg").value),
        "chamfer_top": inputs.itemById("chamfer_top").value * 10.0,
        "chamfer_bottom": inputs.itemById("chamfer_bottom").value * 10.0,
        "chamfer_cyl": inputs.itemById("chamfer_cyl").value * 10.0,
        "chamfer_skirt": inputs.itemById("chamfer_skirt").value * 10.0,
    }


class ExecuteHandler(adsk.core.CommandEventHandler):
    def notify(self, args):
        try:
            app = adsk.core.Application.get()
            design = adsk.fusion.Design.cast(app.activeProduct)
            build(design, read_inputs(args.command.commandInputs))
        except:
            adsk.core.Application.get().userInterface.messageBox(
                "Failed:\n{}".format(traceback.format_exc()))


class CreatedHandler(adsk.core.CommandCreatedEventHandler):
    def notify(self, args):
        i = args.command.commandInputs
        i.addValueInput("u", "U (width units)", "", adsk.core.ValueInput.createByReal(1.0))
        sp = i.addDropDownCommandInput("spacing", "Spacing", adsk.core.DropDownStyles.TextListDropDownStyle)
        sp.listItems.add("choc", True); sp.listItems.add("mx", False)
        st = i.addDropDownCommandInput("stem", "Stem", adsk.core.DropDownStyles.TextListDropDownStyle)
        st.listItems.add("choc", True); st.listItems.add("mx", False)
        tp = i.addDropDownCommandInput("top", "Top", adsk.core.DropDownStyles.TextListDropDownStyle)
        tp.listItems.add("dish", True); tp.listItems.add("bump", False)
        i.addValueInput("skirt_h", "Skirt height", "mm", val(1.7))
        i.addValueInput("taper_h", "Taper height", "mm", val(2.0))
        i.addValueInput("cyl_dia", "Cylinder dia", "mm", val(13.0))
        i.addValueInput("cyl_h", "Cylinder height", "mm", val(1.5))
        i.addValueInput("dish_depth", "Dish/bump depth", "mm", val(0.8))
        i.addValueInput("wall", "Wall thickness", "mm", val(1.2))
        i.addValueInput("draft_deg", "Inner wall draft", "deg", adsk.core.ValueInput.createByString("5 deg"))
        i.addValueInput("chamfer_top", "Chamfer: top perim", "mm", val(0.3))
        i.addValueInput("chamfer_bottom", "Chamfer: bottom edge", "mm", val(0.3))
        i.addValueInput("chamfer_cyl", "Chamfer: cylinder rim", "mm", val(0.3))
        i.addValueInput("chamfer_skirt", "Chamfer: skirt/taper", "mm", val(0.3))
        onExec = ExecuteHandler()
        args.command.execute.add(onExec)
        _handlers.append(onExec)


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        if not adsk.fusion.Design.cast(app.activeProduct):
            ui.messageBox("Open a Fusion Design first.")
            return
        cmd_def = ui.commandDefinitions.itemById("keycapGen")
        if not cmd_def:
            cmd_def = ui.commandDefinitions.addButtonDefinition(
                "keycapGen", "Keycap Generator", "Generate a parametric Choc/MX keycap")
        onCreated = CreatedHandler()
        cmd_def.commandCreated.add(onCreated)
        _handlers.append(onCreated)
        cmd_def.execute()
        adsk.autoTerminate(False)
    except:
        if ui:
            ui.messageBox("Failed:\n{}".format(traceback.format_exc()))
