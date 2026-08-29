#!/usr/bin/env python3
"""Build the smooth-render gallery and its full parameter table."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


PROJECT_DIR = Path(__file__).resolve().parent.parent
MEDIA_DIR = PROJECT_DIR / "media"
IMAGE_DIR = MEDIA_DIR / "catalog_smooth"
MANIFEST_PATH = (
    PROJECT_DIR / "release" / "catalog_permutations" / "catalog-permutations.json"
)
CATALOG_PATH = MEDIA_DIR / "parameter-permutations-smooth-catalog.png"
TABLE_PATH = MEDIA_DIR / "parameter-permutations-table.png"

FONT_PATH = "/System/Library/Fonts/SFNS.ttf"
ROUNDED_FONT_PATH = "/System/Library/Fonts/SFNSRounded.ttf"


def font(size: int, rounded: bool = False) -> ImageFont.FreeTypeFont:
    path = ROUNDED_FONT_PATH if rounded else FONT_PATH
    return ImageFont.truetype(path, size=size)


def title_case(slug: str) -> str:
    return " ".join(word.capitalize() for word in slug.split("-"))


def rounded_mask(size: tuple[int, int], radius: int) -> Image.Image:
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size[0], size[1]), radius, fill=255)
    return mask


def parameter_line(variant: dict) -> str:
    p = variant["parameters"]
    text = (
        f"Dish Ø{p['cyl_dia']:.1f}  ·  depth {p['dish_depth']:.1f}  "
        f"·  skirt/taper {p['skirt_h']:.1f}/{p['taper_h']:.1f} mm"
    )
    if variant["top_style"] == "raised":
        text += f"  ·  top {p['cyl_h']:.1f} mm"
    return text


def draw_section_header(
    draw: ImageDraw.ImageDraw,
    y: int,
    label: str,
    description: str,
    accent: tuple[int, int, int],
) -> None:
    draw.rounded_rectangle((88, y, 103, y + 31), radius=7, fill=accent)
    draw.text((124, y - 5), label, font=font(29, rounded=True), fill=(244, 246, 248))
    draw.text((124, y + 29), description, font=font(18), fill=(142, 149, 157))
    draw.line((780, y + 17, 1960, y + 17), fill=(54, 58, 63), width=2)


def draw_card(canvas: Image.Image, variant: dict, x: int, y: int) -> None:
    draw = ImageDraw.Draw(canvas)
    card_size = (600, 532)
    image_size = (600, 450)
    card_w, card_h = card_size
    image_w, image_h = image_size
    slug = variant["slug"]
    style = variant["top_style"]

    draw.rounded_rectangle(
        (x, y, x + card_w, y + card_h),
        radius=28,
        fill=(20, 22, 25),
        outline=(55, 59, 64),
        width=2,
    )
    source = Image.open(IMAGE_DIR / f"{slug}-smooth-v2.png").convert("RGB")
    image = ImageOps.fit(source, image_size, method=Image.Resampling.LANCZOS)
    canvas.paste(image, (x, y), rounded_mask(image_size, 28))

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


def create_catalog(variants: list[dict]) -> None:
    canvas = Image.new("RGB", (2048, 2560), (12, 14, 17))
    draw = ImageDraw.Draw(canvas)
    x_positions = (88, 724, 1360)
    row_y = (215, 775, 1410, 1970)

    draw.text(
        (88, 45),
        "SMOOTH PARAMETRIC KEYCAPS",
        font=font(48, rounded=True),
        fill=(247, 248, 250),
    )
    draw.text(
        (90, 105),
        "12 exact Fusion variants · satin black surface · no visible print layers",
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

    raised = [item for item in variants if item["top_style"] == "raised"]
    flat = [item for item in variants if item["top_style"] == "flat"]
    for index, variant in enumerate(raised):
        draw_card(canvas, variant, x_positions[index % 3], row_y[index // 3])
    for index, variant in enumerate(flat):
        draw_card(canvas, variant, x_positions[index % 3], row_y[2 + index // 3])

    canvas.save(CATALOG_PATH)


def create_table(variants: list[dict]) -> None:
    width, height = 2048, 1120
    canvas = Image.new("RGB", (width, height), (12, 14, 17))
    draw = ImageDraw.Draw(canvas)

    draw.text(
        (88, 45),
        "PARAMETER TABLE",
        font=font(46, rounded=True),
        fill=(247, 248, 250),
    )
    draw.text(
        (90, 102),
        "All dimensions in millimeters · em dash means the raised top is disabled",
        font=font(21),
        fill=(151, 157, 165),
    )

    columns = [
        ("Variant", 520),
        ("Style", 160),
        ("Skirt H", 150),
        ("Taper H", 150),
        ("Dish Ø", 170),
        ("Top H", 150),
        ("Dish depth", 180),
        ("Wall", 140),
        ("Edge", 140),
    ]
    table_width = sum(column_width for _, column_width in columns)
    left = (width - table_width) // 2
    header_top = 165
    header_height = 70
    row_height = 65

    draw.rounded_rectangle(
        (left, header_top, left + table_width, header_top + header_height),
        radius=18,
        fill=(31, 35, 40),
    )
    x = left
    for label, column_width in columns:
        align_x = x + 18 if label == "Variant" else x + column_width / 2
        draw.text(
            (align_x, header_top + header_height / 2),
            label,
            font=font(20, rounded=True),
            fill=(232, 235, 239),
            anchor="lm" if label == "Variant" else "mm",
        )
        x += column_width

    for index, variant in enumerate(variants):
        row_top = header_top + header_height + index * row_height
        fill = (20, 23, 27) if index % 2 == 0 else (16, 19, 22)
        draw.rectangle((left, row_top, left + table_width, row_top + row_height), fill=fill)

        style = variant["top_style"]
        p = variant["parameters"]
        accent = (229, 157, 83) if style == "raised" else (68, 186, 217)
        cells = [
            title_case(variant["slug"].removeprefix(f"{style}-")),
            style.capitalize(),
            f"{p['skirt_h']:.1f}",
            f"{p['taper_h']:.1f}",
            f"{p['cyl_dia']:.1f}",
            f"{p['cyl_h']:.1f}" if style == "raised" else "—",
            f"{p['dish_depth']:.1f}",
            f"{p['wall']:.1f}",
            f"{p['edge_size']:.2f}",
        ]
        x = left
        for column_index, ((_, column_width), value) in enumerate(zip(columns, cells)):
            align_x = x + 18 if column_index == 0 else x + column_width / 2
            color = accent if column_index == 1 else (221, 224, 228)
            draw.text(
                (align_x, row_top + row_height / 2),
                value,
                font=font(20, rounded=column_index in (0, 1)),
                fill=color,
                anchor="lm" if column_index == 0 else "mm",
            )
            x += column_width
        draw.line(
            (left, row_top + row_height, left + table_width, row_top + row_height),
            fill=(43, 47, 52),
            width=1,
        )

    bottom = header_top + header_height + len(variants) * row_height
    draw.rounded_rectangle(
        (left, header_top, left + table_width, bottom),
        radius=18,
        outline=(62, 67, 73),
        width=2,
    )
    draw.text(
        (left, bottom + 33),
        "Fixed footprint: 17.5 × 16.5 mm  ·  Choc twin-stem geometry",
        font=font(20),
        fill=(139, 146, 154),
    )
    canvas.save(TABLE_PATH)


def main() -> None:
    variants = json.loads(MANIFEST_PATH.read_text())["variants"]
    if len(variants) != 12:
        raise ValueError("Expected 12 catalog variants")
    create_catalog(variants)
    create_table(variants)
    print(CATALOG_PATH)
    print(TABLE_PATH)


if __name__ == "__main__":
    main()
