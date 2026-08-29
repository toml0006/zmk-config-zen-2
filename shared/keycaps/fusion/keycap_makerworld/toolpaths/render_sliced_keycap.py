"""Render the Fusion keycap with layer orientation derived from PrusaSlicer.

Run with Blender, for example:

    blender --background --python render_sliced_keycap.py -- \
        --mesh ../release/MakerWorld_Parametric_Choc_Keycap.stl \
        --gcode MakerWorld_Parametric_Choc_Keycap_edge_0.08mm.gcode \
        --output ../media/sliced-keycap.png

The model is rendered in its normal installed pose. PrusaSlicer sliced the mesh
after a 90-degree X rotation, so its build Z becomes the keycap's Y axis. The
material uses the exact layer pitch reported by the G-code; consequently every
band is the intersection of one global family of parallel build planes with the
entire model instead of a face-by-face image texture.
"""

import argparse
import math
import os
import re
import sys

import bpy
from mathutils import Vector


MOVE_RE = re.compile(r"([XYZEF])(-?(?:\d+(?:\.\d*)?|\.\d+))")


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--mesh", required=True)
    parser.add_argument("--gcode", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--width", type=int, default=1448)
    parser.add_argument("--height", type=int, default=1086)
    parser.add_argument("--proof-output")
    return parser.parse_args(argv)


def parse_prusa_gcode(filename):
    layer_z = []
    paths = []
    active_path = None
    move_type = ""
    current = {"X": None, "Y": None, "Z": 0.0, "E": 0.0}
    absolute_e = True
    layer_height = None

    with open(filename, "r", encoding="utf-8", errors="replace") as stream:
        for raw_line in stream:
            line = raw_line.strip()
            if line.startswith(";TYPE:"):
                move_type = line[6:]
                active_path = None
                continue
            if line.startswith(";Z:"):
                current["Z"] = float(line[3:])
                layer_z.append(current["Z"])
                active_path = None
                continue
            if line.startswith(";HEIGHT:") and layer_height is None:
                layer_height = float(line[8:])
                continue
            if line == "M82":
                absolute_e = True
                continue
            if line == "M83":
                absolute_e = False
                continue
            if line.startswith("G92"):
                values = dict((axis, float(value)) for axis, value in MOVE_RE.findall(line))
                current.update(values)
                active_path = None
                continue
            if not line.startswith(("G0 ", "G1 ")):
                continue

            values = dict((axis, float(value)) for axis, value in MOVE_RE.findall(line))
            old_x, old_y, old_z, old_e = (
                current["X"], current["Y"], current["Z"], current["E"])
            new_x = values.get("X", old_x)
            new_y = values.get("Y", old_y)
            new_z = values.get("Z", old_z)
            requested_e = values.get("E")
            if requested_e is None:
                new_e = old_e
                extruding = False
            elif absolute_e:
                new_e = requested_e
                extruding = new_e > old_e + 1e-8
            else:
                new_e = old_e + requested_e
                extruding = requested_e > 1e-8

            has_xy_move = (
                old_x is not None and old_y is not None and
                new_x is not None and new_y is not None and
                (abs(new_x - old_x) > 1e-8 or abs(new_y - old_y) > 1e-8))

            if move_type == "External perimeter" and extruding and has_xy_move:
                start = (old_x, old_y, old_z)
                end = (new_x, new_y, new_z)
                if active_path is None or active_path[-1] != start:
                    active_path = [start]
                    paths.append(active_path)
                active_path.append(end)
            else:
                active_path = None

            current.update({"X": new_x, "Y": new_y, "Z": new_z, "E": new_e})

    if not layer_z:
        raise RuntimeError("No PrusaSlicer layer heights found in {}".format(filename))
    if not paths:
        raise RuntimeError("No external-perimeter paths found in {}".format(filename))

    unique_layers = sorted(set(round(value, 6) for value in layer_z))
    if layer_height is None and len(unique_layers) > 1:
        layer_height = min(
            b - a for a, b in zip(unique_layers, unique_layers[1:]) if b > a)
    return unique_layers, layer_height or 0.08, paths


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.curves, bpy.data.meshes, bpy.data.materials,
                       bpy.data.cameras, bpy.data.lights):
        for datablock in list(datablocks):
            if datablock.users == 0:
                datablocks.remove(datablock)


def import_mesh(filename):
    bpy.ops.wm.stl_import(filepath=filename)
    obj = bpy.context.selected_objects[0]
    obj.name = "Fusion keycap"
    bounds = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    center_x = (min(p.x for p in bounds) + max(p.x for p in bounds)) / 2
    center_y = (min(p.y for p in bounds) + max(p.y for p in bounds)) / 2
    min_z = min(p.z for p in bounds)
    obj.location += Vector((-center_x, -center_y, -min_z))
    bpy.context.view_layer.update()
    return obj


def keycap_material(layer_height):
    mat = bpy.data.materials.new("Charcoal FDM from Prusa layers")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    output = nodes.new("ShaderNodeOutputMaterial")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Metallic"].default_value = 0.05
    bsdf.inputs["Roughness"].default_value = 0.38

    geometry = nodes.new("ShaderNodeNewGeometry")
    separate = nodes.new("ShaderNodeSeparateXYZ")
    frequency = nodes.new("ShaderNodeMath")
    frequency.operation = "MULTIPLY"
    frequency.inputs[1].default_value = (2 * math.pi) / layer_height
    wave = nodes.new("ShaderNodeMath")
    wave.operation = "SINE"
    normalize = nodes.new("ShaderNodeMath")
    normalize.operation = "MULTIPLY_ADD"
    normalize.inputs[1].default_value = 0.5
    normalize.inputs[2].default_value = 0.5
    layer_color = nodes.new("ShaderNodeMixRGB")
    layer_color.blend_type = "MIX"
    layer_color.inputs[1].default_value = (0.026, 0.03, 0.038, 1)
    layer_color.inputs[2].default_value = (0.044, 0.052, 0.064, 1)
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.2
    bump.inputs["Distance"].default_value = layer_height * 0.1

    # The original model is lying flat. Its Y coordinate is PrusaSlicer's
    # standing build Z after the inverse 90-degree rotation.
    links.new(geometry.outputs["Position"], separate.inputs["Vector"])
    links.new(separate.outputs["Y"], frequency.inputs[0])
    links.new(frequency.outputs[0], wave.inputs[0])
    links.new(wave.outputs[0], bump.inputs["Height"])
    links.new(wave.outputs[0], normalize.inputs[0])
    links.new(normalize.outputs[0], layer_color.inputs[0])
    links.new(layer_color.outputs[0], bsdf.inputs["Base Color"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])
    return mat


def simple_material(name, color, roughness=0.5, metallic=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat


def add_toolpath_curves(paths, mesh_obj, layer_height):
    all_x = [point[0] for path in paths for point in path]
    all_y = [point[1] for path in paths for point in path]
    all_z = [point[2] for path in paths for point in path]
    bed_x = (min(all_x) + max(all_x)) / 2
    bed_y = (min(all_y) + max(all_y)) / 2
    build_z_center = (min(all_z) + max(all_z)) / 2

    mesh_bounds = [mesh_obj.matrix_world @ Vector(corner) for corner in mesh_obj.bound_box]
    mesh_z_center = (min(p.z for p in mesh_bounds) + max(p.z for p in mesh_bounds)) / 2

    curve = bpy.data.curves.new("Prusa external perimeter toolpaths", "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 1
    curve.bevel_depth = layer_height * 0.58
    curve.bevel_resolution = 1
    curve.resolution_v = 1

    for path in paths:
        if len(path) < 2:
            continue
        spline = curve.splines.new("POLY")
        spline.points.add(len(path) - 1)
        for index, (x, y, z) in enumerate(path):
            # Undo PrusaSlicer's X rotation: standing build Z becomes model Y;
            # standing bed Y becomes negative model Z.
            point = (
                x - bed_x,
                z - build_z_center,
                -(y - bed_y) + mesh_z_center,
                1.0,
            )
            spline.points[index].co = point

    obj = bpy.data.objects.new("Actual PrusaSlicer external perimeters", curve)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(simple_material(
        "Extruded filament paths", (0.16, 0.18, 0.22), 0.32, 0.12))
    return obj


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def setup_stage(width, height):
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.image_settings.color_depth = "8"
    scene.render.image_settings.compression = 15
    scene.render.resolution_percentage = 100
    scene.world.color = (0.006, 0.008, 0.012)
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.view_settings.exposure = 1.0

    ground_mat = simple_material("Dark studio ground", (0.008, 0.01, 0.014), 0.43)
    bpy.ops.mesh.primitive_plane_add(size=100, location=(0, 0, -0.08))
    ground = bpy.context.object
    ground.name = "Studio ground"
    ground.data.materials.append(ground_mat)

    aspect = width / height
    camera_distance = 48 if aspect < 1 else 43
    camera = bpy.data.cameras.new("Camera")
    camera.lens = 63
    camera_obj = bpy.data.objects.new("Camera", camera)
    bpy.context.collection.objects.link(camera_obj)
    camera_obj.location = (-camera_distance * 0.64, -camera_distance * 0.72,
                           camera_distance * 0.58)
    look_at(camera_obj, (0, 0, 2.7))
    scene.camera = camera_obj

    def area_light(name, location, color, energy, size):
        data = bpy.data.lights.new(name, "AREA")
        data.color = color
        data.energy = energy
        data.shape = "DISK"
        data.size = size
        obj = bpy.data.objects.new(name, data)
        bpy.context.collection.objects.link(obj)
        obj.location = location
        look_at(obj, (0, 0, 2.5))
        return obj

    area_light("Warm key", (-18, -20, 28), (1.0, 0.48, 0.22), 2800, 16)
    area_light("Cyan rim", (20, 7, 14), (0.05, 0.58, 1.0), 2500, 12)
    area_light("Soft top", (-2, 3, 30), (0.55, 0.68, 1.0), 1900, 20)
    return scene


def render(scene, filename):
    os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
    scene.render.filepath = os.path.abspath(filename)
    bpy.ops.render.render(write_still=True)


def main():
    args = parse_args()
    layers, layer_height, paths = parse_prusa_gcode(args.gcode)
    clear_scene()
    keycap = import_mesh(args.mesh)
    keycap.data.materials.clear()
    keycap.data.materials.append(keycap_material(layer_height))
    toolpaths = add_toolpath_curves(paths, keycap, layer_height)
    toolpaths.hide_render = True
    scene = setup_stage(args.width, args.height)
    render(scene, args.output)

    if args.proof_output:
        keycap.hide_render = True
        toolpaths.hide_render = False
        render(scene, args.proof_output)

    print("Prusa layers: {} at {:.3f} mm".format(len(layers), layer_height))
    print("External-perimeter polylines: {}".format(len(paths)))
    print("Render: {}".format(os.path.abspath(args.output)))
    if args.proof_output:
        print("Toolpath proof: {}".format(os.path.abspath(args.proof_output)))


if __name__ == "__main__":
    main()
