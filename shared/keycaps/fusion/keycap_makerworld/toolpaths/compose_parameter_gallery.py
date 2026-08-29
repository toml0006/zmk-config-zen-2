"""Compose the exact CAD-style preset renders into a MakerWorld gallery."""

import argparse
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont


PRESETS = (
    ("default", "DEFAULT", "Balanced baseline"),
    ("minimum", "ALL MINIMUM", "Every public parameter at minimum"),
    ("maximum", "ALL MAXIMUM", "Every public parameter at maximum"),
    ("thin-tall", "THIN / TALL", "Min wall + dish; max heights"),
    ("thick-short", "THICK / SHORT", "Max wall + dish; min heights"),
    ("edge-stress", "EDGE STRESS", "Max edge; min fingertip height"),
)


def font(size, bold=False):
    candidates = (
        "/System/Library/Fonts/SFNS.ttf" if not bold else
        "/System/Library/Fonts/SFNSRounded.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial.ttf",
    )
    for candidate in candidates:
        if os.path.exists(candidate):
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()


def rounded_image(image, size, radius):
    image = image.resize(size, Image.Resampling.LANCZOS)
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size[0], size[1]), radius, fill=255)
    result = Image.new("RGB", size, "white")
    result.paste(image.convert("RGB"), mask=mask)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    width, height = 1448, 1086
    canvas = Image.new("RGB", (width, height), "#eef3fb")
    draw = ImageDraw.Draw(canvas)

    title_font = font(45, bold=True)
    subtitle_font = font(21)
    label_font = font(23, bold=True)
    detail_font = font(16)
    draw.text((62, 38), "PARAMETER PRESET GALLERY", fill="#10244f", font=title_font)
    draw.text(
        (64, 96),
        "Exact Fusion exports · one orthographic camera · common scale",
        fill="#53647f",
        font=subtitle_font,
    )

    card_width, card_height = 424, 410
    image_width, image_height = 400, 300
    column_gap, row_gap = 28, 28
    start_x, start_y = 60, 148

    for index, (slug, label, detail) in enumerate(PRESETS):
        row, column = divmod(index, 3)
        x = start_x + column * (card_width + column_gap)
        y = start_y + row * (card_height + row_gap)

        shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow)
        shadow_draw.rounded_rectangle(
            (x + 3, y + 8, x + card_width + 3, y + card_height + 8),
            22,
            fill=(36, 58, 98, 34),
        )
        shadow = shadow.filter(ImageFilter.GaussianBlur(10))
        canvas.paste(shadow, (0, 0), shadow)
        draw = ImageDraw.Draw(canvas)
        draw.rounded_rectangle(
            (x, y, x + card_width, y + card_height),
            22,
            fill="#ffffff",
            outline="#cfdaeb",
            width=2,
        )

        image_path = os.path.join(args.input_dir, "parameter-{}-cad-4x3.png".format(slug))
        render = Image.open(image_path)
        card_render = rounded_image(render, (image_width, image_height), 14)
        canvas.paste(card_render, (x + 12, y + 12))
        draw = ImageDraw.Draw(canvas)
        draw.text((x + 20, y + 327), label, fill="#112653", font=label_font)
        draw.text((x + 20, y + 365), detail, fill="#64738b", font=detail_font)

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    canvas.save(args.output, optimize=True)


if __name__ == "__main__":
    main()
