"""Build and export the MakerWorld-ready parametric Choc keycap.

MakerWorld does not execute Fusion scripts. This script creates the release
artifact MakerWorld consumes: a single-body F3D with design history enabled
and the complete set of geometry-safe numeric controls favorited for the
MakerWorld customizer.

Run from Fusion's Scripts and Add-Ins dialog. A new document is created, built,
validated, and exported to release/MakerWorld_Parametric_Choc_Keycap.f3d.
"""

import json
import importlib
import os
import sys
import traceback

import adsk.core
import adsk.fusion


HERE = os.path.dirname(os.path.realpath(__file__))
GENERATOR_DIR = os.path.normpath(os.path.join(HERE, "..", "keycap_1u_choc"))
RELEASE_DIR = os.path.join(HERE, "release")
RELEASE_FILE = os.path.join(RELEASE_DIR, "MakerWorld_Parametric_Choc_Keycap.f3d")
MESH_FILE = os.path.join(RELEASE_DIR, "MakerWorld_Parametric_Choc_Keycap.stl")
VARIANT_DIR = os.path.join(RELEASE_DIR, "parameter_variants")
FLAT_DISH_DIR = os.path.join(RELEASE_DIR, "flat_dish_variants")
CATALOG_DIR = os.path.join(RELEASE_DIR, "catalog_permutations")
CATALOG_MANIFEST = os.path.join(CATALOG_DIR, "catalog-permutations.json")
CONTRACT_FILE = os.path.join(HERE, "makerworld-inputs.json")
CATALOG_ONLY = False

if GENERATOR_DIR not in sys.path:
    sys.path.insert(0, GENERATOR_DIR)

import keycap_1u_choc as generator

# Fusion keeps imported script modules alive between runs. Reload the shared
# generator so iterative edits (including topology switches) are honored.
generator = importlib.reload(generator)


MODEL_VALUES = {
    "U": 1.0,
    "spacing": "choc",
    "stem": "choc",
    "top": "dish",
    "edge": "chamfer",
    "homing": "none",
    "homing_pos": "center",
    "homing_count": 1,
    "orient_for_print": True,
    "skirt_h": 1.7,
    "taper_h": 2.0,
    "cyl_dia": 13.0,
    "cyl_h": 1.5,
    "dish_depth": 0.8,
    "sweep": 0.0,
    "wall": 1.2,
    "draft_deg": 0.0,
    "chamfer_top": 0.3,
    "chamfer_bottom": 0.3,
    "chamfer_cyl": 0.3,
    "chamfer_skirt": 0.3,
}

FLAT_DISH_PRESETS = (
    ("shallow", {
        "skirt_h": 1.5,
        "taper_h": 1.7,
        "cyl_dia": 11.5,
        "dish_depth": 0.4,
    }),
    ("standard", {
        "skirt_h": 1.7,
        "taper_h": 2.0,
        "cyl_dia": 13.0,
        "dish_depth": 0.8,
    }),
    ("wide-deep", {
        "skirt_h": 2.0,
        "taper_h": 2.4,
        "cyl_dia": 13.4,
        "dish_depth": 1.2,
    }),
)

CATALOG_PRESETS = (
    ("raised-compact-shallow", True, {
        "skirt_h": 1.2, "taper_h": 1.5, "cyl_dia": 11.0,
        "cyl_h": 0.8, "dish_depth": 0.3, "wall": 0.9,
        "edge_size": 0.15,
    }),
    ("raised-compact-deep", True, {
        "skirt_h": 1.2, "taper_h": 1.5, "cyl_dia": 12.0,
        "cyl_h": 1.0, "dish_depth": 1.2, "wall": 1.2,
        "edge_size": 0.30,
    }),
    ("raised-wide-low", True, {
        "skirt_h": 1.7, "taper_h": 1.5, "cyl_dia": 13.4,
        "cyl_h": 0.8, "dish_depth": 0.8, "wall": 1.2,
        "edge_size": 0.45,
    }),
    ("raised-balanced", True, {
        "skirt_h": 1.7, "taper_h": 2.0, "cyl_dia": 13.0,
        "cyl_h": 1.5, "dish_depth": 0.8, "wall": 1.2,
        "edge_size": 0.30,
    }),
    ("raised-tall-narrow", True, {
        "skirt_h": 2.4, "taper_h": 3.0, "cyl_dia": 11.0,
        "cyl_h": 2.5, "dish_depth": 0.5, "wall": 0.9,
        "edge_size": 0.30,
    }),
    ("raised-tall-wide-deep", True, {
        "skirt_h": 2.4, "taper_h": 3.0, "cyl_dia": 13.4,
        "cyl_h": 2.5, "dish_depth": 1.2, "wall": 1.5,
        "edge_size": 0.45,
    }),
    ("flat-compact-shallow", False, {
        "skirt_h": 1.2, "taper_h": 1.5, "cyl_dia": 11.0,
        "cyl_h": 0.8, "dish_depth": 0.3, "wall": 0.9,
        "edge_size": 0.15,
    }),
    ("flat-compact-deep", False, {
        "skirt_h": 1.2, "taper_h": 1.5, "cyl_dia": 12.0,
        "cyl_h": 0.8, "dish_depth": 1.2, "wall": 1.5,
        "edge_size": 0.30,
    }),
    ("flat-wide-shallow", False, {
        "skirt_h": 1.7, "taper_h": 2.0, "cyl_dia": 13.4,
        "cyl_h": 0.8, "dish_depth": 0.3, "wall": 1.2,
        "edge_size": 0.30,
    }),
    ("flat-balanced", False, {
        "skirt_h": 1.7, "taper_h": 2.0, "cyl_dia": 13.0,
        "cyl_h": 0.8, "dish_depth": 0.8, "wall": 1.2,
        "edge_size": 0.30,
    }),
    ("flat-tall-narrow", False, {
        "skirt_h": 2.4, "taper_h": 3.0, "cyl_dia": 11.0,
        "cyl_h": 0.8, "dish_depth": 0.8, "wall": 1.2,
        "edge_size": 0.45,
    }),
    ("flat-tall-wide-deep", False, {
        "skirt_h": 2.4, "taper_h": 3.0, "cyl_dia": 13.4,
        "cyl_h": 0.8, "dish_depth": 1.2, "wall": 1.5,
        "edge_size": 0.45,
    }),
)

PUBLIC_PARAMETERS = {
    "skirt_h": "Height of the straight lower skirt. Recommended 1.2-2.4 mm.",
    "taper_h": "Height of the tapered body. Recommended 1.5-3.0 mm.",
    "cyl_dia": "Diameter of the circular fingertip surface. Recommended 11.0-13.4 mm.",
    "cyl_h": "Height of the circular top above the tapered body. Recommended 0.8-2.5 mm.",
    "dish_depth": "Depth of the spherical dish. Must stay above zero; recommended 0.3-1.2 mm.",
    "sweep": "Signed front/back angle of the complete upper surface. Zero is level; use the opposite sign to reverse direction. Recommended -10 to 10 degrees.",
    "wall": "Shell wall thickness. Recommended 0.9-1.5 mm.",
    "chamfer_top": "Edge treatment around the tapered body's upper perimeter. Recommended 0.15-0.45 mm.",
    "chamfer_bottom": "Edge treatment around the bottom perimeter. Recommended 0.15-0.45 mm.",
    "chamfer_cyl": "Edge treatment around the circular fingertip rim. Recommended 0.15-0.45 mm.",
    "chamfer_skirt": "Edge treatment at the skirt-to-taper transition. Recommended 0.15-0.45 mm.",
}

CHAMFER_PARAMETERS = (
    "chamfer_top",
    "chamfer_bottom",
    "chamfer_cyl",
    "chamfer_skirt",
)


def ensure_parameter(design, name, expression, unit, comment):
    parameter = design.userParameters.itemByName(name)
    if parameter is None:
        parameter = design.userParameters.add(
            name,
            adsk.core.ValueInput.createByString(expression),
            unit,
            comment,
        )
    else:
        parameter.expression = expression
        parameter.comment = comment
    return parameter


def configure_parameters(design):
    for parameter in design.userParameters:
        parameter.isFavorite = False

    for name, comment in PUBLIC_PARAMETERS.items():
        parameter = design.userParameters.itemByName(name)
        if parameter is None:
            raise RuntimeError("Required MakerWorld parameter is missing: {}".format(name))
        parameter.comment = comment
        parameter.isFavorite = True

    dish_radius = design.userParameters.itemByName("dish_r")
    if dish_radius:
        dish_radius.comment = "Derived spherical radius; not exposed in MakerWorld."
        dish_radius.isFavorite = False



def load_contract():
    with open(CONTRACT_FILE, "r", encoding="utf-8") as contract_file:
        return json.load(contract_file)


def validate_design(design, label):
    if not design.computeAll():
        failed_features = []
        error_state = adsk.fusion.FeatureHealthStates.ErrorFeatureHealthState
        for timeline_index in range(design.timeline.count):
            timeline_item = design.timeline.item(timeline_index)
            if timeline_item.healthState == error_state:
                entity_name = ""
                try:
                    entity_name = timeline_item.entity.name
                except:
                    pass
                failed_features.append(
                    "#{} {} {}".format(
                        timeline_index,
                        entity_name,
                        timeline_item.errorOrWarningMessage,
                    ))
        raise RuntimeError(
            "Fusion could not recompute parameter set '{}'. {}".format(
                label, "; ".join(failed_features)))

    component = design.rootComponent
    if component.bRepBodies.count != 1:
        body_details = []
        for body_index in range(component.bRepBodies.count):
            candidate = component.bRepBodies.item(body_index)
            bounds = candidate.boundingBox
            body_details.append(
                "{} [{:.2f},{:.2f},{:.2f}] to [{:.2f},{:.2f},{:.2f}]".format(
                    candidate.name,
                    bounds.minPoint.x * 10.0,
                    bounds.minPoint.y * 10.0,
                    bounds.minPoint.z * 10.0,
                    bounds.maxPoint.x * 10.0,
                    bounds.maxPoint.y * 10.0,
                    bounds.maxPoint.z * 10.0,
                ))
        raise RuntimeError(
            "Parameter set '{}' produced {} bodies; expected one. {}".format(
                label, component.bRepBodies.count, "; ".join(body_details)))

    body = component.bRepBodies.item(0)
    if body.volume <= 0:
        raise RuntimeError("Parameter set '{}' has no measurable volume.".format(label))

    bounds = body.boundingBox
    depth = bounds.maxPoint.y - bounds.minPoint.y
    print_height = bounds.maxPoint.z - bounds.minPoint.z
    if print_height <= depth:
        raise RuntimeError(
            "Parameter set '{}' is not standing on its side: Y={:.3f} mm, "
            "Z={:.3f} mm.".format(label, depth * 10.0, print_height * 10.0))
    if abs(bounds.minPoint.z) > 0.01:
        raise RuntimeError(
            "Parameter set '{}' is not seated on the build plane: min Z={:.3f} mm."
            .format(label, bounds.minPoint.z * 10.0))

    error_state = adsk.fusion.FeatureHealthStates.ErrorFeatureHealthState
    timeline_errors = []
    for index in range(design.timeline.count):
        timeline_object = design.timeline.item(index)
        if timeline_object.healthState == error_state:
            timeline_errors.append(
                "#{} {}".format(index, timeline_object.errorOrWarningMessage))
    if timeline_errors:
        raise RuntimeError(
            "Parameter set '{}' has timeline errors:\n{}".format(
                label, "\n".join(timeline_errors)))

    if component.features.shellFeatures.count != 0:
        raise RuntimeError(
            "The upper keycap must remain solid; no full-height shell feature is allowed.")
    if component.features.extrudeFeatures.itemByName("Fixed-height lower cavity") is None:
        raise RuntimeError("The release is missing its fixed-height lower cavity.")

    fixed_stem_dimensions = {
        "stem_total_h": 3.1,
        "stem_protrude": 1.4,
        "stem_mount_h": 1.7,
    }
    for name, expected_mm in fixed_stem_dimensions.items():
        parameter = design.userParameters.itemByName(name)
        if parameter is None:
            raise RuntimeError("The release is missing fixed stem parameter '{}'.".format(name))
        actual_mm = parameter.value * 10.0
        if abs(actual_mm - expected_mm) > 1e-6:
            raise RuntimeError(
                "Fixed stem parameter '{}' is {:.3f} mm; expected {:.3f} mm."
                .format(name, actual_mm, expected_mm))
        if parameter.isFavorite:
            raise RuntimeError(
                "Fixed stem parameter '{}' must not be exposed in MakerWorld."
                .format(name))
    if component.features.chamferFeatures.count < 1:
        raise RuntimeError("Chamfer controls are exposed, but no chamfer feature was created.")

    favorite_names = {
        parameter.name
        for parameter in design.userParameters
        if parameter.isFavorite
    }
    expected_names = set(PUBLIC_PARAMETERS)
    if favorite_names != expected_names:
        raise RuntimeError(
            "Favorite parameter mismatch. Expected {}; found {}.".format(
                sorted(expected_names), sorted(favorite_names)))

    undriven = []
    for name in expected_names:
        parameter = design.userParameters.itemByName(name)
        if len(parameter.dependentParameters) == 0:
            undriven.append(name)
    if undriven:
        raise RuntimeError(
            "Favorite parameters do not drive model data: {}.".format(
                ", ".join(sorted(undriven))))

    body.name = "MakerWorld_Parametric_Choc_Keycap"


def set_parameter_values(design, inputs, values):
    for item in inputs:
        name = item["name"]
        value = values.get(name, item["default"])
        parameter = design.userParameters.itemByName(name)
        if parameter is None:
            raise RuntimeError("Contract parameter is missing from Fusion: {}".format(name))
        parameter.expression = "{} {}".format(value, item["unit"])


def parameter_cases(inputs):
    """Return the six validated presets used for testing and render exports."""
    defaults = {item["name"]: item["default"] for item in inputs}
    minimums = {item["name"]: item["minimum"] for item in inputs}
    maximums = {item["name"]: item["maximum"] for item in inputs}
    thin_tall = dict(defaults)
    thick_short = dict(defaults)
    edge_stress = dict(defaults)

    for name in ("wall", "dish_depth"):
        thin_tall[name] = minimums[name]
        thick_short[name] = maximums[name]
    for name in ("skirt_h", "taper_h", "cyl_h"):
        thin_tall[name] = maximums[name]
        thick_short[name] = minimums[name]
    for name in CHAMFER_PARAMETERS:
        edge_stress[name] = maximums[name]
    edge_stress["cyl_h"] = minimums["cyl_h"]

    return (
        ("default", "default", defaults),
        ("minimum", "minimum", minimums),
        ("maximum", "maximum", maximums),
        ("thin/tall", "thin-tall", thin_tall),
        ("thick/short", "thick-short", thick_short),
        ("edge stress", "edge-stress", edge_stress),
    )


def exercise_parameter_sets(design):
    contract = load_contract()
    inputs = contract["inputs"]
    contract_names = {item["name"] for item in inputs}
    if contract_names != set(PUBLIC_PARAMETERS):
        raise RuntimeError(
            "makerworld-inputs.json and PUBLIC_PARAMETERS disagree: {} vs {}".format(
                sorted(contract_names), sorted(PUBLIC_PARAMETERS)))

    cases = parameter_cases(inputs)
    for label, _, values in cases:
        set_parameter_values(design, inputs, values)
        validate_design(design, label)

    defaults = cases[0][2]
    set_parameter_values(design, inputs, defaults)
    validate_design(design, "restored defaults")
    return [label for label, _, _ in cases]


def export_release(design):
    os.makedirs(RELEASE_DIR, exist_ok=True)
    staged_file = RELEASE_FILE + ".staged.f3d"
    if os.path.exists(staged_file):
        os.remove(staged_file)
    export_manager = design.exportManager
    options = export_manager.createFusionArchiveExportOptions(staged_file)
    if options is None or not export_manager.execute(options):
        raise RuntimeError("Fusion failed to export {}".format(staged_file))
    os.replace(staged_file, RELEASE_FILE)
    return RELEASE_FILE


def export_stl(design, filename):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    staged_file = filename + ".staged.stl"
    if os.path.exists(staged_file):
        os.remove(staged_file)

    body = design.rootComponent.bRepBodies.item(0)
    export_manager = design.exportManager
    options = export_manager.createSTLExportOptions(body, staged_file)
    if options is None:
        raise RuntimeError("Fusion could not configure STL export.")
    options.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
    options.isBinaryFormat = True
    if not export_manager.execute(options):
        raise RuntimeError("Fusion failed to export {}".format(staged_file))

    os.replace(staged_file, filename)
    return filename


def export_mesh(design):
    return export_stl(design, MESH_FILE)


def export_parameter_variants(design):
    """Export exact STL geometry for every validated parameter preset."""
    inputs = load_contract()["inputs"]
    cases = parameter_cases(inputs)
    exported = []
    for label, slug, values in cases:
        set_parameter_values(design, inputs, values)
        validate_design(design, "{} export".format(label))
        filename = os.path.join(
            VARIANT_DIR,
            "MakerWorld_Parametric_Choc_Keycap_{}.stl".format(slug),
        )
        exported.append(export_stl(design, filename))

    set_parameter_values(design, inputs, cases[0][2])
    validate_design(design, "restored defaults after variant export")
    return exported


def validate_variant_design(design, label):
    if not design.computeAll():
        raise RuntimeError("Fusion could not recompute variant '{}'.".format(label))
    component = design.rootComponent
    if component.bRepBodies.count != 1:
        raise RuntimeError(
            "Variant '{}' produced {} bodies; expected one.".format(
                label, component.bRepBodies.count))
    body = component.bRepBodies.item(0)
    if body.volume <= 0:
        raise RuntimeError("Variant '{}' has no measurable volume.".format(label))

    error_state = adsk.fusion.FeatureHealthStates.ErrorFeatureHealthState
    errors = []
    for index in range(design.timeline.count):
        timeline_object = design.timeline.item(index)
        if timeline_object.healthState == error_state:
            errors.append("#{} {}".format(
                index, timeline_object.errorOrWarningMessage))
    if errors:
        raise RuntimeError(
            "Variant '{}' has timeline errors:\n{}".format(
                label, "\n".join(errors)))
    body.name = "MakerWorld_Choc_Keycap_{}".format(label)


def export_flat_dish_variants(app):
    """Build exact no-pedestal variants with the dish cut into the top face."""
    exported = []
    for slug, overrides in FLAT_DISH_PRESETS:
        document = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        try:
            design = adsk.fusion.Design.cast(app.activeProduct)
            if design is None:
                raise RuntimeError("Fusion did not create the flat-dish design '{}'.".format(slug))
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            values = dict(MODEL_VALUES)
            values.update(overrides)
            values["raised_top"] = False
            generator.build(design, values)
            validate_variant_design(design, slug)
            filename = os.path.join(
                FLAT_DISH_DIR,
                "MakerWorld_Flat_Dish_Choc_Keycap_{}.stl".format(slug),
            )
            exported.append(export_stl(design, filename))
        finally:
            document.close(False)
    return exported


def export_catalog_permutations(app):
    """Export a balanced raised/flat catalog for the realistic image set."""
    exported = []
    manifest = []
    for slug, raised_top, parameters in CATALOG_PRESETS:
        document = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        try:
            design = adsk.fusion.Design.cast(app.activeProduct)
            if design is None:
                raise RuntimeError("Fusion did not create catalog variant '{}'.".format(slug))
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            values = dict(MODEL_VALUES)
            values.update({
                name: value for name, value in parameters.items()
                if name != "edge_size"
            })
            edge_size = parameters["edge_size"]
            for name in CHAMFER_PARAMETERS:
                values[name] = edge_size
            values["raised_top"] = raised_top
            generator.build(design, values)
            validate_variant_design(design, slug)
            filename = os.path.join(
                CATALOG_DIR,
                "MakerWorld_Choc_Keycap_{}.stl".format(slug),
            )
            exported.append(export_stl(design, filename))
            manifest.append({
                "slug": slug,
                "top_style": "raised" if raised_top else "flat",
                "parameters": dict(parameters),
                "stl": os.path.basename(filename),
            })
        finally:
            document.close(False)

    os.makedirs(CATALOG_DIR, exist_ok=True)
    with open(CATALOG_MANIFEST, "w", encoding="utf-8") as manifest_file:
        json.dump({"variants": manifest}, manifest_file, indent=2, sort_keys=True)
        manifest_file.write("\n")
    return exported


def run(context):
    global generator
    # Scripts and Add-Ins can invoke this module repeatedly without re-running
    # its top level. Reload here as well so generator edits are never stale.
    generator = importlib.reload(generator)
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        if CATALOG_ONLY:
            catalog_files = export_catalog_permutations(app)
            ui.messageBox(
                "Catalog permutations exported successfully.\n\n"
                "Variants: {}\n"
                "Directory: {}".format(len(catalog_files), CATALOG_DIR))
            return
        app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        design = adsk.fusion.Design.cast(app.activeProduct)
        if design is None:
            raise RuntimeError("Fusion did not create a Design document.")

        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        generator.build(design, dict(MODEL_VALUES))
        configure_parameters(design)
        validated_sets = exercise_parameter_sets(design)
        release_file = export_release(design)
        mesh_file = export_mesh(design)
        variant_files = export_parameter_variants(design)
        flat_dish_files = export_flat_dish_variants(app)

        ui.messageBox(
            "MakerWorld keycap built successfully.\n\n"
            "F3D: {}\n"
            "STL: {}\n"
            "Orientation: standing on side\n"
            "Parameter STL variants: {}\n"
            "Flat-dish STL variants: {}\n"
            "Validated: {}\n\n"
            "Upload this file as a Raw Model File, then configure the "
            "parameter ranges from makerworld-inputs.json.".format(
                release_file, mesh_file, len(variant_files), len(flat_dish_files),
                ", ".join(validated_sets)))
    except Exception:
        if ui:
            ui.messageBox(
                "MakerWorld keycap build failed:\n{}".format(traceback.format_exc()))
        else:
            raise
