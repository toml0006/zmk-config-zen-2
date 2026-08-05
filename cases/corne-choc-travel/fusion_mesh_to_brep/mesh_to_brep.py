"""
Mesh -> editable B-Rep solid, inside Fusion.

Imports an STL/OBJ/3MF as a mesh body, generates face groups, then runs
Fusion's Mesh Convert in Prismatic mode. Prismatic fits real analytic
surfaces (planes, cylinders) to the facet clusters, so the result has a
handful of editable faces instead of one face per triangle.

Contrast with ../stl_to_step.py (FreeCAD): that produces a valid solid but
one B-Rep face per mesh triangle, which cannot be push/pulled or filleted.

Run inside Fusion: Utilities -> Add-Ins -> Scripts and Add-Ins (Shift+S)
-> My Scripts -> + -> select this folder -> Run.

Leave stl_path empty to get a file picker.
"""

import os
import traceback

import adsk.core
import adsk.fusion

# --------------------------------------------------------------------------
# PARAMETERS
# --------------------------------------------------------------------------
PARAMS = {
    # Source mesh. Empty string -> file picker dialog.
    'stl_path': '/Users/jackson/Downloads/3D-Prints/keyboards/'
                'typeractive-corne-choc/stl/case-bottom-3dp-meshopt.stl',

    # Units the mesh file is authored in: mm | cm | m | in | ft
    'units': 'mm',

    # prismatic -> planes/cylinders/cones fitted to face groups (CAD parts).
    # faceted   -> one B-Rep face per triangle (fast, not editable).
    # organic   -> freeform surfaces (scans, sculpted shapes).
    'method': 'prismatic',

    # Face groups partition the mesh into regions that each become one face.
    # Prismatic conversion needs them; generate unless the mesh already has
    # them (3MF from Fusion sometimes does).
    'generate_face_groups': True,

    # accurate -> surface-fit based, better on machined/printed parts.
    # fast     -> normal-angle based, tune angle_threshold_deg below.
    'face_group_method': 'accurate',

    # accurate only: how far a facet may sit off the fitted surface (mm).
    # Raise it to merge more aggressively, lower it to preserve detail.
    'boundary_tolerance_mm': 0.1,

    # fast only.
    'angle_threshold_deg': 20.0,
    'min_face_group_size': 10,

    # organic only: low | medium | high | precise
    'organic_accuracy': 'high',

    # Convert inside the timeline (True) or as a one-shot base feature (False).
    'parametric': True,
}

MESH_UNITS = {
    'cm': adsk.fusion.MeshUnits.CentimeterMeshUnit,
    'mm': adsk.fusion.MeshUnits.MillimeterMeshUnit,
    'm': adsk.fusion.MeshUnits.MeterMeshUnit,
    'in': adsk.fusion.MeshUnits.InchMeshUnit,
    'ft': adsk.fusion.MeshUnits.FootMeshUnit,
}

CONVERT_METHODS = {
    'faceted': adsk.fusion.MeshConvertMethodTypes.FacetedMeshConvertMethodType,
    'prismatic': adsk.fusion.MeshConvertMethodTypes.PrismaticMeshConvertMethodType,
    'organic': adsk.fusion.MeshConvertMethodTypes.OrganicMeshConvertMethodType,
}

ORGANIC_ACCURACY = {
    'low': adsk.fusion.MeshConvertAccuracyTypes.LowMeshConvertAccuracyType,
    'medium': adsk.fusion.MeshConvertAccuracyTypes.MediumMeshConvertAccuracyType,
    'high': adsk.fusion.MeshConvertAccuracyTypes.HighMeshConvertAccuracyType,
    'precise': adsk.fusion.MeshConvertAccuracyTypes.PreciseMeshConvertAccuracyType,
}


def pick_file(ui):
    dlg = ui.createFileDialog()
    dlg.title = 'Select mesh to convert'
    dlg.filter = 'Mesh files (*.stl;*.obj;*.3mf);;All files (*.*)'
    if dlg.showOpen() != adsk.core.DialogResults.DialogOK:
        return None
    return dlg.filename


def import_mesh(design, root, path, units, parametric):
    """Return the imported MeshBody. Parametric designs need a base feature."""
    if not parametric:
        return root.meshBodies.add(path, units)[0]

    base = root.features.baseFeatures.add()
    base.startEdit()
    try:
        bodies = root.meshBodies.add(path, units, base)
    finally:
        base.finishEdit()
    if not bodies or len(bodies) == 0:
        raise RuntimeError('mesh import returned no bodies')
    return bodies[0]


def generate_face_groups(root, mesh_body):
    feats = root.features.meshGenerateFaceGroupsFeatures
    fg_input = feats.createInput(mesh_body)

    if PARAMS['face_group_method'] == 'fast':
        fg_input.meshGenerateFaceGroupsMethodType = \
            adsk.fusion.MeshGenerateFaceGroupsMethodTypes.FastGenerateFaceGroupsType
        fg_input.angleThreshold = adsk.core.ValueInput.createByString(
            '%s deg' % PARAMS['angle_threshold_deg'])
        fg_input.minimumFaceGroupSize = adsk.core.ValueInput.createByReal(
            float(PARAMS['min_face_group_size']))
    else:
        fg_input.meshGenerateFaceGroupsMethodType = \
            adsk.fusion.MeshGenerateFaceGroupsMethodTypes.AccurateGenerateFaceGroupsType
        fg_input.boundaryTolerance = adsk.core.ValueInput.createByString(
            '%s mm' % PARAMS['boundary_tolerance_mm'])

    feats.add(fg_input)


def convert_mesh(root, mesh_body):
    feats = root.features.meshConvertFeatures
    try:
        cv_input = feats.createInput([mesh_body])
    except Exception:
        # Older builds want an ObjectCollection instead of a plain list.
        coll = adsk.core.ObjectCollection.create()
        coll.add(mesh_body)
        cv_input = feats.createInput(coll)

    cv_input.meshConvertMethodType = CONVERT_METHODS[PARAMS['method']]

    if PARAMS['method'] == 'organic':
        cv_input.meshConvertResolutionType = \
            adsk.fusion.MeshConvertResolutionTypes.ByAccuracyMeshConvertResolutionType
        cv_input.meshConvertAccuracyType = \
            ORGANIC_ACCURACY[PARAMS['organic_accuracy']]

    cv_input.meshConvertOperationType = (
        adsk.fusion.MeshConvertOperationTypes.ParametricFeatureMeshConvertOperationType
        if PARAMS['parametric'] else
        adsk.fusion.MeshConvertOperationTypes.BaseFeatureMeshConvertOperationType)

    feats.add(cv_input)


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface

        path = PARAMS['stl_path'] or pick_file(ui)
        if not path:
            return
        if not os.path.isfile(path):
            ui.messageBox('Mesh not found:\n%s' % path)
            return

        units = MESH_UNITS.get(PARAMS['units'])
        if units is None:
            ui.messageBox('Unknown units %r. Use one of: %s'
                          % (PARAMS['units'], ', '.join(MESH_UNITS)))
            return
        if PARAMS['method'] not in CONVERT_METHODS:
            ui.messageBox('Unknown method %r. Use one of: %s'
                          % (PARAMS['method'], ', '.join(CONVERT_METHODS)))
            return

        doc = app.documents.add(
            adsk.core.DocumentTypes.FusionDesignDocumentType)
        design = adsk.fusion.Design.cast(app.activeProduct)
        design.designType = (
            adsk.fusion.DesignTypes.ParametricDesignType if PARAMS['parametric']
            else adsk.fusion.DesignTypes.DirectDesignType)
        root = design.rootComponent

        name = os.path.splitext(os.path.basename(path))[0]
        doc.name = '%s (brep)' % name

        mesh_body = import_mesh(design, root, path, units, PARAMS['parametric'])
        mesh_body.name = name
        facets = mesh_body.mesh.triangleCount

        if PARAMS['generate_face_groups'] and PARAMS['method'] != 'faceted':
            generate_face_groups(root, mesh_body)

        convert_mesh(root, mesh_body)
        adsk.doEvents()

        solids = [b for b in root.bRepBodies if b.isSolid]
        if not solids:
            ui.messageBox(
                'Conversion produced no solid body.\n\n'
                'Mesh: %s (%d facets)\n\n'
                'Try raising boundary_tolerance_mm, or set method to '
                '"organic" if the shape is freeform.' % (name, facets))
            return

        body = max(solids, key=lambda b: b.volume)
        body.name = name
        ui.messageBox(
            'Converted %s\n\n'
            '  method:  %s\n'
            '  facets:  %d\n'
            '  faces:   %d\n'
            '  edges:   %d\n'
            '  volume:  %.1f mm^3\n\n'
            'Body is a solid — push/pull faces, add sketches and fillets as '
            'usual. Export via File -> Export -> STEP.'
            % (name, PARAMS['method'], facets, body.faces.count,
               body.edges.count, body.volume * 1000.0))

    except Exception:
        if ui:
            ui.messageBox('Failed:\n%s' % traceback.format_exc())
