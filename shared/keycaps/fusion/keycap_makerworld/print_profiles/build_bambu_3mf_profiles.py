#!/usr/bin/env python3
"""Build the catalog permutations as sliced Bambu Studio 3MF projects.

The release catalog STLs are already rotated onto their intended print edge.
This script combines each one with a fully resolved
Bambu Lab A1 mini 0.2 mm / PLA Matte profile, enables normal automatic
supports, slices it, exports a Bambu project 3MF, and then validates the
settings embedded in the archive.

In addition to the twelve one-cap projects, the release includes a sampler
project with all twelve configurations arranged and sliced on one plate.

Set BAMBU_STUDIO_BIN to override automatic Bambu Studio discovery.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import zipfile
import xml.etree.ElementTree as ET

from PIL import Image, ImageOps


HERE = Path(__file__).resolve().parent
PROJECT_DIR = HERE.parent
MANIFEST_FILE = (
    PROJECT_DIR / "release" / "catalog_permutations" / "catalog-permutations.json"
)
CATALOG_STL_DIR = PROJECT_DIR / "release" / "catalog_permutations"
PROFILE_IMAGE_DIR = PROJECT_DIR / "media" / "catalog_smooth"
COMBINED_PROFILE_IMAGE = (
    PROJECT_DIR / "media" / "parameter-permutations-smooth-catalog.png"
)
OUTPUT_DIR = PROJECT_DIR / "release" / "print_profiles"
OUTPUT_MANIFEST = OUTPUT_DIR / "bambu-3mf-profiles.json"
PROFILE_IMAGE_ARCHIVE_PATH = "Metadata/profile_image.png"
COMBINED_PROFILE_FILENAME = (
    "MakerWorld_Choc_Keycap_12_Config_Sampler_A1mini_0.08mm.3mf"
)


def catalog_stl(slug: str) -> Path:
    return CATALOG_STL_DIR / f"MakerWorld_Choc_Keycap_{slug}.stl"

MACHINE_NAME = "Bambu Lab A1 mini 0.2 nozzle"
PROCESS_NAME = "0.08mm High Quality @BBL A1M 0.2 nozzle"
FILAMENT_NAME = "Bambu PLA Matte @BBL A1M"

EXPECTED_SETTINGS = {
    "printer_settings_id": MACHINE_NAME,
    "print_settings_id": PROCESS_NAME,
    "layer_height": "0.08",
    "initial_layer_print_height": "0.1",
    "wall_loops": "3",
    "sparse_infill_density": "100%",
    "sparse_infill_pattern": "zig-zag",
    "brim_type": "outer_only",
    "brim_width": "3",
    "enable_support": "1",
    "support_type": "normal(auto)",
    "support_style": "default",
    "support_on_build_plate_only": "0",
}

REQUIRED_ARCHIVE_FILES = {
    "3D/3dmodel.model",
    "Metadata/model_settings.config",
    "Metadata/plate_1.gcode",
    "Metadata/plate_1.gcode.md5",
    "Metadata/plate_1.png",
    "Metadata/plate_1_small.png",
    PROFILE_IMAGE_ARCHIVE_PATH,
    "Metadata/project_settings.config",
    "Metadata/slice_info.config",
}


def find_bambu_studio() -> Path:
    override = os.environ.get("BAMBU_STUDIO_BIN")
    candidates = [
        Path(override) if override else None,
        Path(
            "/tmp/codex-bambu-3mf-profiles/mount/"
            "BambuStudio.app/Contents/MacOS/BambuStudio"
        ),
        Path("/Applications/BambuStudio.app/Contents/MacOS/BambuStudio"),
    ]
    for candidate in candidates:
        if candidate and candidate.is_file():
            return candidate
    raise RuntimeError(
        "Bambu Studio was not found. Install it or set BAMBU_STUDIO_BIN."
    )


def profile_root(binary: Path) -> Path:
    root = binary.parent.parent / "Resources" / "profiles" / "BBL"
    if not root.is_dir():
        raise RuntimeError(f"Bambu profile resources were not found under {root}")
    return root


def bambu_version(binary: Path) -> str:
    result = subprocess.run(
        [str(binary), "--help"],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    match = re.search(r"BambuStudio-([0-9.]+)", result.stdout + result.stderr)
    return match.group(1) if match else "unknown"


def index_profiles(directory: Path) -> dict[str, tuple[Path, dict]]:
    profiles: dict[str, tuple[Path, dict]] = {}
    for path in directory.glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        name = data.get("name")
        if name:
            profiles[name] = (path, data)
    return profiles


def resolve_profile(directory: Path, name: str) -> dict:
    profiles = index_profiles(directory)
    cache: dict[str, dict] = {}

    def resolve(current: str, stack: tuple[str, ...] = ()) -> dict:
        if current in cache:
            return dict(cache[current])
        if current in stack:
            raise RuntimeError(f"Circular Bambu profile inheritance: {stack + (current,)}")
        if current not in profiles:
            raise RuntimeError(f"Bambu profile '{current}' was not found in {directory}")

        _, child = profiles[current]
        merged: dict = {}
        parent = child.get("inherits")
        if parent:
            merged.update(resolve(parent, stack + (current,)))
        merged.update(child)
        merged.pop("inherits", None)
        cache[current] = merged
        return dict(merged)

    return resolve(name)


def write_json(path: Path, data: dict) -> None:
    path.write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def square_thumbnail(source: Image.Image, size: int) -> bytes:
    """Return a dark, square PNG that preserves the complete 4:3 render."""
    canvas = Image.new("RGBA", (size, size), (24, 25, 27, 255))
    fitted = ImageOps.contain(source.convert("RGBA"), (size, size), Image.Resampling.LANCZOS)
    offset = ((size - fitted.width) // 2, (size - fitted.height) // 2)
    canvas.alpha_composite(fitted, offset)
    output = io.BytesIO()
    canvas.save(output, format="PNG", optimize=True)
    return output.getvalue()


def attach_profile_image_path(project: Path, image_path: Path) -> Path:
    """Embed a gallery render and use it as the plate thumbnail."""
    if not image_path.is_file():
        raise RuntimeError(f"Missing profile image: {image_path}")

    source_bytes = image_path.read_bytes()
    with Image.open(io.BytesIO(source_bytes)) as source:
        replacements = {
            "Metadata/plate_1.png": square_thumbnail(source, 512),
            "Metadata/plate_1_small.png": square_thumbnail(source, 128),
            PROFILE_IMAGE_ARCHIVE_PATH: source_bytes,
        }

    staged = project.with_suffix(".image-staged.3mf")
    if staged.exists():
        staged.unlink()
    with zipfile.ZipFile(project, "r") as original, zipfile.ZipFile(
        staged, "w", compression=zipfile.ZIP_DEFLATED
    ) as updated:
        for item in original.infolist():
            if item.filename not in replacements:
                updated.writestr(item, original.read(item.filename))
        for name, data in replacements.items():
            updated.writestr(name, data)
    staged.replace(project)
    return image_path


def attach_profile_image(project: Path, slug: str) -> Path:
    """Embed the matching gallery render and use it as the plate thumbnail."""
    return attach_profile_image_path(
        project,
        PROFILE_IMAGE_DIR / f"{slug}-smooth-v2.png",
    )


def run_profile(
    binary: Path,
    work_dir: Path,
    machine_file: Path,
    process_file: Path,
    filament_file: Path,
    slug: str,
) -> Path:
    oriented_stl = catalog_stl(slug)
    if not oriented_stl.is_file():
        raise RuntimeError(f"Missing edge-oriented catalog STL: {oriented_stl}")

    final_file = OUTPUT_DIR / f"MakerWorld_Choc_Keycap_{slug}_A1mini_0.08mm.3mf"
    staged_file = work_dir / final_file.name

    command = [
        str(binary),
        "--debug",
        "2",
        "--arrange",
        "1",
        "--ensure-on-bed",
        "--curr-bed-type=Textured PEI Plate",
        "--load-settings",
        f"{machine_file};{process_file}",
        "--load-filaments",
        str(filament_file),
        "--wall-loops=3",
        "--sparse-infill-density=100%",
        "--sparse-infill-pattern=zig-zag",
        "--brim-type=outer_only",
        "--brim-width=3",
        "--enable-support=1",
        "--support-type=normal(auto)",
        "--support-style=default",
        "--support-on-build-plate-only=0",
        "--seam-position=back",
        "--slice",
        "0",
        "--export-3mf",
        str(staged_file),
        str(oriented_stl),
    ]
    result = subprocess.run(
        command,
        cwd=work_dir,
        capture_output=True,
        text=True,
        timeout=360,
        check=False,
    )
    if result.returncode != 0 or not staged_file.is_file():
        raise RuntimeError(
            f"Bambu Studio failed for {slug} (exit {result.returncode}).\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )

    final_file.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(staged_file, final_file)
    return final_file


def run_combined_profile(
    binary: Path,
    work_dir: Path,
    machine_file: Path,
    process_file: Path,
    filament_file: Path,
    slugs: list[str],
) -> Path:
    oriented_stls = [catalog_stl(slug) for slug in slugs]
    missing = [path for path in oriented_stls if not path.is_file()]
    if missing:
        raise RuntimeError(f"Missing edge-oriented catalog STLs: {missing}")

    final_file = OUTPUT_DIR / COMBINED_PROFILE_FILENAME
    staged_file = work_dir / final_file.name
    command = [
        str(binary),
        "--debug",
        "2",
        "--arrange",
        "1",
        "--ensure-on-bed",
        "--curr-bed-type=Textured PEI Plate",
        "--load-settings",
        f"{machine_file};{process_file}",
        "--load-filaments",
        str(filament_file),
        "--wall-loops=3",
        "--sparse-infill-density=100%",
        "--sparse-infill-pattern=zig-zag",
        "--brim-type=outer_only",
        "--brim-width=3",
        "--enable-support=1",
        "--support-type=normal(auto)",
        "--support-style=default",
        "--support-on-build-plate-only=0",
        "--seam-position=back",
        "--slice",
        "0",
        "--export-3mf",
        str(staged_file),
        *[str(path) for path in oriented_stls],
    ]
    result = subprocess.run(
        command,
        cwd=work_dir,
        capture_output=True,
        text=True,
        timeout=900,
        check=False,
    )
    if result.returncode != 0 or not staged_file.is_file():
        raise RuntimeError(
            f"Bambu Studio failed for the combined sampler (exit {result.returncode}).\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )

    final_file.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(staged_file, final_file)
    return final_file


def read_project_settings(archive: zipfile.ZipFile) -> dict:
    return json.loads(archive.read("Metadata/project_settings.config"))


def validate_profile(
    path: Path,
    image_path: Path,
    expected_object_count: int = 1,
) -> dict:
    with zipfile.ZipFile(path) as archive:
        names = set(archive.namelist())
        missing = REQUIRED_ARCHIVE_FILES - names
        if missing:
            raise RuntimeError(f"{path.name} is missing archive entries: {sorted(missing)}")

        gcode = archive.read("Metadata/plate_1.gcode")
        if len(gcode) < 10_000:
            raise RuntimeError(f"{path.name} does not contain a meaningful sliced plate")

        settings = read_project_settings(archive)
        for key, expected in EXPECTED_SETTINGS.items():
            actual = settings.get(key)
            if str(actual) != expected:
                raise RuntimeError(
                    f"{path.name}: {key} is {actual!r}; expected {expected!r}"
                )
        filament_ids = settings.get("filament_settings_id")
        if filament_ids != [FILAMENT_NAME]:
            raise RuntimeError(
                f"{path.name}: unexpected filament settings {filament_ids!r}"
            )

        slice_root = ET.fromstring(archive.read("Metadata/slice_info.config"))
        plates = slice_root.findall("plate")
        if len(plates) != 1:
            raise RuntimeError(f"{path.name}: expected one plate, found {len(plates)}")
        objects = plates[0].findall("object")
        if len(objects) != expected_object_count:
            raise RuntimeError(
                f"{path.name}: expected {expected_object_count} objects, "
                f"found {len(objects)}"
            )
        metadata = {
            item.attrib.get("key"): item.attrib.get("value")
            for item in plates[0].findall("metadata")
        }
        if metadata.get("outside") != "false":
            raise RuntimeError(f"{path.name}: object is outside the build plate")
        if metadata.get("support_used") != "true":
            raise RuntimeError(f"{path.name}: normal supports were enabled but not generated")
        if archive.read(PROFILE_IMAGE_ARCHIVE_PATH) != image_path.read_bytes():
            raise RuntimeError(f"{path.name}: embedded profile image does not match {image_path.name}")

        with Image.open(io.BytesIO(archive.read("Metadata/plate_1.png"))) as thumbnail:
            if thumbnail.size != (512, 512):
                raise RuntimeError(f"{path.name}: invalid plate thumbnail size {thumbnail.size}")

    return {
        "bytes": path.stat().st_size,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "prediction_seconds": int(metadata.get("prediction", "0")),
        "support_used": metadata.get("support_used") == "true",
        "profile_image": image_path.name,
        "profile_image_sha256": hashlib.sha256(image_path.read_bytes()).hexdigest(),
    }


def main() -> None:
    binary = find_bambu_studio()
    version = bambu_version(binary)
    force_rebuild = os.environ.get("KEYCAP_FORCE_REBUILD") == "1"
    resources = profile_root(binary)
    source_manifest = json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))
    variants = source_manifest.get("variants", [])
    if len(variants) != 12:
        raise RuntimeError(f"Expected 12 catalog permutations, found {len(variants)}")

    machine = resolve_profile(resources / "machine", MACHINE_NAME)
    process = resolve_profile(resources / "process", PROCESS_NAME)
    filament = resolve_profile(resources / "filament", FILAMENT_NAME)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    built = []
    combined_profile = None
    with tempfile.TemporaryDirectory(prefix="keycap-bambu-profiles-") as temp_name:
        work_dir = Path(temp_name)
        machine_file = work_dir / "machine.json"
        process_file = work_dir / "process.json"
        filament_file = work_dir / "filament.json"
        write_json(machine_file, machine)
        write_json(process_file, process)
        write_json(filament_file, filament)

        for variant in variants:
            slug = variant["slug"]
            existing_profile = (
                OUTPUT_DIR / f"MakerWorld_Choc_Keycap_{slug}_A1mini_0.08mm.3mf"
            )
            existing_image = PROFILE_IMAGE_DIR / f"{slug}-smooth-v2.png"
            source_stl = catalog_stl(slug)
            source_is_older = (
                source_stl.is_file()
                and existing_profile.is_file()
                and existing_profile.stat().st_mtime_ns >= source_stl.stat().st_mtime_ns
            )
            if not force_rebuild and source_is_older and existing_image.is_file():
                try:
                    validation = validate_profile(existing_profile, existing_image)
                except RuntimeError:
                    pass
                else:
                    built.append(
                        {
                            "file": existing_profile.name,
                            "slug": slug,
                            "top_style": variant["top_style"],
                            "parameters": variant["parameters"],
                            **validation,
                        }
                    )
                    print(f"reused validated {existing_profile.name}")
                    continue
            profile = run_profile(
                binary,
                work_dir,
                machine_file,
                process_file,
                filament_file,
                slug,
            )
            profile_image = attach_profile_image(profile, slug)
            validation = validate_profile(profile, profile_image)
            built.append(
                {
                    "file": profile.name,
                    "slug": slug,
                    "top_style": variant["top_style"],
                    "parameters": variant["parameters"],
                    **validation,
                }
            )
            print(f"validated {profile.name}")

        slugs = [variant["slug"] for variant in variants]
        combined_path = OUTPUT_DIR / COMBINED_PROFILE_FILENAME
        source_stls = [catalog_stl(slug) for slug in slugs]
        combined_sources_are_older = (
            combined_path.is_file()
            and all(path.is_file() for path in source_stls)
            and combined_path.stat().st_mtime_ns
            >= max(path.stat().st_mtime_ns for path in source_stls)
        )
        if (
            not force_rebuild
            and combined_sources_are_older
            and COMBINED_PROFILE_IMAGE.is_file()
        ):
            try:
                combined_validation = validate_profile(
                    combined_path,
                    COMBINED_PROFILE_IMAGE,
                    expected_object_count=len(slugs),
                )
            except RuntimeError:
                pass
            else:
                combined_profile = {
                    "file": combined_path.name,
                    "slug": "12-config-sampler",
                    "object_count": len(slugs),
                    "configurations": slugs,
                    **combined_validation,
                }
                print(f"reused validated {combined_path.name}")

        if combined_profile is None:
            combined_path = run_combined_profile(
                binary,
                work_dir,
                machine_file,
                process_file,
                filament_file,
                slugs,
            )
            combined_image = attach_profile_image_path(
                combined_path,
                COMBINED_PROFILE_IMAGE,
            )
            combined_validation = validate_profile(
                combined_path,
                combined_image,
                expected_object_count=len(slugs),
            )
            combined_profile = {
                "file": combined_path.name,
                "slug": "12-config-sampler",
                "object_count": len(slugs),
                "configurations": slugs,
                **combined_validation,
            }
            print(f"validated {combined_path.name}")

    release_manifest = {
        "schemaVersion": 1,
        "slicer": f"Bambu Studio {version}",
        "printer": MACHINE_NAME,
        "process": PROCESS_NAME,
        "filament": FILAMENT_NAME,
        "orientation": "standing on edge",
        "settings": {
            "nozzle_mm": 0.2,
            "layer_height_mm": 0.08,
            "initial_layer_height_mm": 0.1,
            "wall_loops": 3,
            "infill": "100%",
            "brim_mm": 3,
            "supports": "normal (auto)",
            "plate": "Textured PEI Plate",
        },
        "profiles": built,
        "combined_profile": combined_profile,
    }
    write_json(OUTPUT_MANIFEST, release_manifest)
    print(f"wrote {len(built)} individual profiles and one combined profile to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
