#!/usr/bin/env python3
"""Compose the photoreal parameter permutations into a labeled catalog sheet."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


PROJECT_DIR = Path(__file__).resolve().parent.parent
MEDIA_DIR = PROJECT_DIR / "media"
IMAGE_DIR = MEDIA_DIR / "catalog_photoreal"
MANIFEST_PATH = (
    PROJECT_DIR / "release" / "catalog_permutations" / "catalog-permutations.json"
)
OUTPUT_PATH = MEDIA_DIR / "parameter-permutations-photoreal-catalog.png"

CANVAS_SIZE = (2048, 2560)
CARD_SIZE = (600, 532)
IMAGE_SIZE = (600, 450)
X_POSITIONS = (88, 724, 1360)
ROW_Y = (215, 775, 1410, 1970)

FONT_PATH = "/System/Library/Fonts/SFNS.ttf"
ROUNDED_FONT_PATH = "/System/Library/Fonts/SFNSRounded.ttf"


def font(size: int, rounded: bool = False) -> ImageFont.FreeTypeFont:
    path = ROUNDED_FONT_PATH if rounded else FONT_PATH
    return ImageFont.truetype(path, size=size)


def title_case(slug: str) -> str:
    return " ".join(word.capitalize() for word in slug.split("-"))


def parameter_line(variant: dict) -> str:
    params = variant["parameters"]
    base = (
        f"Dish Ø{params['cyl_dia']:.1f}  ·  depth {params['dish_depth']:.1f}  "
        f"·  skirt/taper {params['skirt_h']:.1f}/{params['taper_h']:.1f} mm"
    )
    if variant["top_style"] == "raised":
        return f"{base}  ·  top {params['cyl_h']:.1f} mm"
    return base


def rounded_mask(size: tuple[int, int], radius: int) -> Image.Image:
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size[0], size[1]), radius, fill=255)
    return mask


def paste_card(canvas: Image.Image, variant: dict, x: int, y: int) -> None:
    draw = ImageDraw.Draw(canvas)
    card_w, card_h = CARD_SIZE
    image_w, image_h = IMAGE_SIZE
    slug = variant["slug"]
    style = variant["top_style"]

    draw.rounded_rectangle(
        (x, y, x + card_w, y + card_h),
        radius=28,
        fill=(20, 22, 25),
        outline=(55, 59, 64),
        width=2,
    )

    source = Image.open(IMAGE_DIR / f"{slug}-photoreal-v1.png").convert("RGB")
    image = ImageOps.fit(source, IMAGE_SIZE, method=Image.Resampling.LANCZOS)
    canvas.paste(image, (x, y), rounded_mask(IMAGE_SIZE, 28))

    accent = (229, 157, 83) if style == "raised" else (68, 186, 217)
    draw.rounded_rectangle(
        (x + 18, y + image_h + 16, x + 104, y + image_h + 47),
        radius=15,
        fill=accent,
    )
    draw.text(
        (x + 61, y + image_h + 31),
        style.upper(),
        font=font(15, rounded=True),
        fill=(10, 12, 14),
        anchor="mm",
    )
    draw.text(
        (x + 118, y + image_h + 14),
        title_case(slug.removeprefix(f"{style}-")),
        font=font(25, rounded=True),
        fill=(245, 246, 248),
    )
    draw.text(
        (x + 18, y + image_h + 54),
        parameter_line(variant),
        font=font(16),
        fill=(164, 170, 178),
    )


def draw_section_header(
    draw: ImageDraw.ImageDraw, y: int, label: str, description: str, accent: tuple[int, int, int]
) -> None:
    draw.rounded_rectangle((88, y, 103, y + 31), radius=7, fill=accent)
    draw.text((124, y - 5), label, font=font(29, rounded=True), fill=(244, 246, 248))
    draw.text((124, y + 29), description, font=font(18), fill=(142, 149, 157))
    draw.line((780, y + 17, 1960, y + 17), fill=(54, 58, 63), width=2)


def main() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text())
    variants = manifest["variants"]
    raised = [item for item in variants if item["top_style"] == "raised"]
    flat = [item for item in variants if item["top_style"] == "flat"]

    if len(raised) != 6 or len(flat) != 6:
        raise ValueError("Expected six raised and six flat catalog variants")

    canvas = Image.new("RGB", CANVAS_SIZE, (12, 14, 17))
    draw = ImageDraw.Draw(canvas)

    draw.text(
        (88, 45),
        "PARAMETRIC KEYCAP PERMUTATIONS",
        font=font(48, rounded=True),
        fill=(247, 248, 250),
    )
    draw.text(
        (90, 105),
        "12 exact Fusion variants · edge-oriented Prusa geometry · black PLA studio treatment",
        font=font(22),
        fill=(151, 157, 165),
    )

    draw_section_header(
        draw,
        158,
        "RAISED PLATFORM",
        "Dish cut into a configurable circular top",
        (229, 157, 83),
    )
    draw_section_header(
        draw,
        1353,
        "FLAT FACE",
        "Dish cut directly into the continuous upper face",
        (68, 186, 217),
    )

    for index, variant in enumerate(raised):
        paste_card(canvas, variant, X_POSITIONS[index % 3], ROW_Y[index // 3])
    for index, variant in enumerate(flat):
        paste_card(canvas, variant, X_POSITIONS[index % 3], ROW_Y[2 + index // 3])

    canvas.save(OUTPUT_PATH, quality=95)
    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()
