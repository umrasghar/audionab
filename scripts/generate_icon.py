"""Generate AudioNab app icons using Pillow.

Produces:
    assets/icon.ico      - Multi-resolution Windows icon (16..256px)
    assets/icon-256.png  - 256px PNG for README / GitHub
    assets/icon-64.png   - 64px PNG for system tray

Usage:
    python scripts/generate_icon.py
"""

import os
import sys
from pathlib import Path

from PIL import Image, ImageDraw


# Brand colors
BLUE = "#7aa2f7"
BLUE_DARK = "#5b86d4"
WHITE = "#ffffff"


def _hex_to_rgb(hex_color):
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def draw_icon(size=512):
    """Draw the AudioNab icon at the given size and return a PIL Image."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    blue = _hex_to_rgb(BLUE)
    blue_dark = _hex_to_rgb(BLUE_DARK)
    white = _hex_to_rgb(WHITE)

    # --- Rounded rectangle background ---
    margin = int(size * 0.04)
    radius = int(size * 0.18)
    draw.rounded_rectangle(
        [margin, margin, size - margin - 1, size - margin - 1],
        radius=radius,
        fill=blue,
        outline=blue_dark,
        width=max(2, size // 128),
    )

    # --- Stylized "A" ---
    cx = size * 0.44  # shift left slightly to make room for waves
    cy = size * 0.52

    # "A" dimensions
    a_half_w = size * 0.20
    a_top = size * 0.18
    a_bottom = size * 0.78

    # Outer triangle
    draw.polygon(
        [
            (cx, a_top),
            (cx - a_half_w, a_bottom),
            (cx + a_half_w, a_bottom),
        ],
        fill=white,
    )

    # Inner cutout triangle
    inner_half_w = a_half_w * 0.45
    inner_top = cy - size * 0.02
    inner_bottom = a_bottom
    draw.polygon(
        [
            (cx, inner_top),
            (cx - inner_half_w, inner_bottom),
            (cx + inner_half_w, inner_bottom),
        ],
        fill=blue,
    )

    # Horizontal crossbar
    bar_y = cy + size * 0.08
    bar_h = size * 0.055
    bar_half_w = a_half_w * 0.82
    draw.rectangle(
        [cx - bar_half_w, bar_y, cx + bar_half_w, bar_y + bar_h],
        fill=white,
    )

    # --- Audio wave bars (right side) ---
    wave_x = cx + a_half_w + size * 0.08
    wave_w = size * 0.04
    wave_r = max(2, size // 128)

    # Three bars at different heights and lengths
    bars = [
        (cy - size * 0.12, size * 0.10),  # top bar (short)
        (cy + size * 0.01, size * 0.16),   # middle bar (long)
        (cy + size * 0.14, size * 0.08),   # bottom bar (shortest)
    ]
    for bar_cy, bar_len in bars:
        draw.rounded_rectangle(
            [wave_x, bar_cy, wave_x + bar_len, bar_cy + wave_w],
            radius=wave_r,
            fill=white,
        )

    return img


def main():
    project_root = Path(__file__).resolve().parent.parent
    assets_dir = project_root / "assets"
    assets_dir.mkdir(exist_ok=True)

    print("  Generating AudioNab icons...")

    # Draw at 512px for quality
    master = draw_icon(512)

    # Save multi-resolution ICO
    ico_sizes = [16, 32, 48, 64, 128, 256]
    ico_images = []
    for s in ico_sizes:
        resized = master.resize((s, s), Image.LANCZOS)
        ico_images.append(resized)

    ico_path = assets_dir / "icon.ico"
    ico_images[0].save(
        str(ico_path),
        format="ICO",
        append_images=ico_images[1:],
        sizes=[(s, s) for s in ico_sizes],
    )
    print(f"    icon.ico ({', '.join(f'{s}px' for s in ico_sizes)})")

    # Save 256px PNG
    png_256 = master.resize((256, 256), Image.LANCZOS)
    png_256_path = assets_dir / "icon-256.png"
    png_256.save(str(png_256_path), format="PNG")
    print(f"    icon-256.png")

    # Save 64px PNG
    png_64 = master.resize((64, 64), Image.LANCZOS)
    png_64_path = assets_dir / "icon-64.png"
    png_64.save(str(png_64_path), format="PNG")
    print(f"    icon-64.png")

    print(f"  Done! Icons saved to {assets_dir}")


if __name__ == "__main__":
    main()
