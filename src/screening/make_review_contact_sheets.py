#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Convert Step 3B.2 21-band annual RGB review GeoTIFFs into labelled PNG contact
sheets. This is visualization only; it does not calculate NDVI/NDMI or choose
controls.

Expected band order:
  2020 R,G,B ... 2026 R,G,B
"""

import argparse
from pathlib import Path
import re
import numpy as np
import rasterio
from PIL import Image, ImageDraw, ImageFont

YEARS = list(range(2020, 2027))

def stretch_rgb(arr, lo=200.0, hi=3500.0, gamma=1.0):
    """Fixed stretch so years are visually comparable."""
    x = np.asarray(arr, dtype=np.float32)
    x = np.clip((x - lo) / (hi - lo), 0, 1)
    if gamma != 1.0:
        x = np.power(x, 1.0 / gamma)
    x = (x * 255.0).round().astype(np.uint8)
    return x

def site_id_from_name(path):
    stem = path.stem
    m = re.search(r"RGB_REVIEW_(.+)$", stem)
    return m.group(1) if m else stem

def build_one(path, outdir, lo, hi, gamma, scale):
    with rasterio.open(path) as ds:
        if ds.count < 21:
            raise RuntimeError(f"{path.name}: expected >=21 bands, got {ds.count}")

        panels = []
        for i, year in enumerate(YEARS):
            bands = [1 + i*3, 2 + i*3, 3 + i*3]
            rgb = ds.read(bands)
            rgb = np.moveaxis(rgb, 0, -1)
            rgb = stretch_rgb(rgb, lo=lo, hi=hi, gamma=gamma)
            img = Image.fromarray(rgb, mode="RGB")

            if scale != 1:
                img = img.resize(
                    (img.width * scale, img.height * scale),
                    resample=Image.Resampling.NEAREST
                )
            panels.append((year, img))

    site = site_id_from_name(path)
    pad = 12
    label_h = 28

    pw = max(img.width for _, img in panels)
    ph = max(img.height for _, img in panels)

    cols, rows = 4, 2
    title_h = 38

    canvas = Image.new(
        "RGB",
        (
            pad + cols * (pw + pad),
            title_h + rows * (ph + label_h + pad) + pad
        ),
        "white"
    )
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()

    draw.text(
        (pad, 10),
        f"{site} — Sentinel-2 annual RGB median review",
        fill="black",
        font=font
    )

    for idx, (year, img) in enumerate(panels):
        row, col = divmod(idx, cols)
        x = pad + col * (pw + pad)
        y = title_h + row * (ph + label_h + pad)
        canvas.paste(img, (x, y))
        label = str(year)
        if year == 2026:
            label += " (through 2026-09-28)"
        draw.text((x, y + ph + 5), label, fill="black", font=font)

    out = outdir / f"{site}_review_contact_sheet.png"
    canvas.save(out)
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input-dir", required=True)
    ap.add_argument("--outdir", default="review_contact_sheets")
    ap.add_argument("--min", type=float, default=200.0,
                    help="fixed reflectance stretch minimum")
    ap.add_argument("--max", type=float, default=3500.0,
                    help="fixed reflectance stretch maximum")
    ap.add_argument("--gamma", type=float, default=1.0)
    ap.add_argument("--scale", type=int, default=4,
                    help="nearest-neighbour display enlargement")
    args = ap.parse_args()

    input_dir = Path(args.input_dir)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    files = sorted(input_dir.glob("SC0002_STEP3B2_RGB_REVIEW_*.tif"))
    if not files:
        files = sorted(input_dir.glob("*.tif"))

    if not files:
        raise SystemExit("No GeoTIFF files found.")

    print(f"Found {len(files)} GeoTIFFs.")
    for p in files:
        out = build_one(
            p, outdir,
            lo=args.min, hi=args.max,
            gamma=args.gamma, scale=args.scale
        )
        print(f"[OK] {p.name} -> {out.name}")

    print("\nThese PNGs are visual screening aids only.")
    print("Do not use display stretch or apparent greenness as an outcome score.")

if __name__ == "__main__":
    main()
