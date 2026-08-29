"""Render exact Fusion parameter-preset STLs as clean CAD-style cards.

Run with Blender, for example:

    blender --background --python render_parameter_variants.py -- \
        --input-dir ../release/parameter_variants \
        --output-dir ../media/parameter_presets

All variants use the same orthographic camera, scale, material, and lighting so
their visible size and profile differences can be compared directly.
"""

import argparse
import os
import sys

import bpy
from mathutils import Vector


PRESETS = (
    "default",
    "minimum",
    "maximum",
    "thin-tall",
    "thick-short",
    "edge-stress",
)


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--width", type=int, default=1200)
    parser.add_argument("--height", type=int, default=900)
    return parser.parse_args(argv)


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (
            bpy.data.curves,
            bpy.data.meshes,
            bpy.data.materials,
            bpy.data.cameras,
            bpy.data.lights):
        for datablock in list(datablocks):
            if datablock.users == 0:
                datablocks.remove(datablock)


def simple_material(name, color, roughness):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = 0.0
    return material


def look_at(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def import_centered_mesh(filename):
    bpy.ops.wm.stl_import(filepath=filename)
    obj = bpy.context.selected_objects[0]
    obj.name = os.path.splitext(os.path.basename(filename))[0]

    bounds = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    center_x = (min(point.x for point in bounds) + max(point.x for point in bounds)) / 2
    center_y = (min(point.y for point in bounds) + max(point.y for point in bounds)) / 2
    min_z = min(point.z for point in bounds)
    obj.location += Vector((-center_x, -center_y, -min_z))
    bpy.context.view_layer.update()

    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    obj.data.materials.append(simple_material(
        "CAD blue", (0.075, 0.265, 0.72), 0.46))
    return obj


def add_area_light(name, location, energy, size, color):
    data = bpy.data.lights.new(name, "AREA")
    data.energy = energy
    data.shape = "DISK"
    data.size = size
    data.color = color
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    look_at(obj, (0, 0, 3.0))


def setup_scene(width, height, model_height):
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.image_settings.color_depth = "8"
    scene.render.image_settings.compression = 15
    scene.render.film_transparent = False
    scene.world.color = (0.82, 0.855, 0.92)
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.view_settings.exposure = 0.65

    ground = simple_material("Drafting surface", (0.89, 0.915, 0.96), 0.72)
    bpy.ops.mesh.primitive_plane_add(size=80, location=(0, 0, -0.06))
    bpy.context.object.data.materials.append(ground)

    camera_data = bpy.data.cameras.new("Orthographic comparison camera")
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = 28.0
    camera_obj = bpy.data.objects.new("Orthographic comparison camera", camera_data)
    bpy.context.collection.objects.link(camera_obj)
    camera_obj.location = (25.0, -31.0, 23.0)
    look_at(camera_obj, (0, 0, max(model_height * 0.42, 2.3)))
    scene.camera = camera_obj

    add_area_light("Large soft key", (-20, -24, 30), 1050, 14,
                   (1.0, 0.94, 0.84))
    add_area_light("Cool fill", (20, -4, 18), 800, 12,
                   (0.55, 0.72, 1.0))
    add_area_light("Top rim", (0, 18, 28), 900, 11,
                   (0.78, 0.88, 1.0))

    # A restrained outline makes the output read as a technical rendering,
    # while the shaded faces continue to come directly from the exported STL.
    scene.render.use_freestyle = True
    line_settings = scene.view_layers[0].freestyle_settings.linesets[0].linestyle
    line_settings.color = (0.025, 0.055, 0.13)
    line_settings.thickness = 1.15
    return scene


def render_preset(input_dir, output_dir, preset, width, height):
    clear_scene()
    mesh_path = os.path.join(
        input_dir,
        "MakerWorld_Parametric_Choc_Keycap_{}.stl".format(preset),
    )
    obj = import_centered_mesh(mesh_path)
    bounds = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    model_height = max(point.z for point in bounds) - min(point.z for point in bounds)
    scene = setup_scene(width, height, model_height)
    output_path = os.path.join(output_dir, "parameter-{}-cad-4x3.png".format(preset))
    scene.render.filepath = os.path.abspath(output_path)
    bpy.ops.render.render(write_still=True)
    print("Rendered {} -> {}".format(preset, output_path))


def main():
    args = parse_args()
    os.makedirs(args.output_dir, exist_ok=True)
    for preset in PRESETS:
        render_preset(
            os.path.abspath(args.input_dir),
            os.path.abspath(args.output_dir),
            preset,
            args.width,
            args.height,
        )


if __name__ == "__main__":
    main()
