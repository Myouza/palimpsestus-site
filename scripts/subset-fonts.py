#!/usr/bin/env python3
"""
subset-fonts.py — Build-time font subsetting for Palimpsestus

Scans all MDX content files, identifies characters outside the coverage
of Google Fonts CDN (CJK Extension B, etc.), and generates minimal
woff2 subsets from full source fonts stored on the server.

Generates one woff2 per (range, weight) combination so that headings,
body text, and bold all render with the correct native weight rather
than relying on browser-synthesized faux bold.

Usage:
    python3 subset-fonts.py <content_dir> <output_dir>

Example:
    python3 subset-fonts.py ./src/content/novel ./public/fonts

Requires: fonttools, brotli (pip install fonttools brotli)
Source fonts expected at: /opt/palimpsestus/fonts/
"""

import sys
import os
import glob
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
FONT_DIR = "/opt/palimpsestus/fonts"

# Character ranges that need local font coverage.
# Each range can have multiple weight variants.
RANGES = {
    "CJKExtB-Serif": {
        "start": 0x20000,
        "end": 0x2A6DF,
        "label": "CJK Extension B",
        "weights": {
            200: "NotoSerifCJKsc-ExtraLight.otf",
            300: "NotoSerifCJKsc-Light.otf",
            400: "NotoSerifCJKsc-Regular.otf",
            500: "NotoSerifCJKsc-Medium.otf",
            600: "NotoSerifCJKsc-SemiBold.otf",
            700: "NotoSerifCJKsc-Bold.otf",
            900: "NotoSerifCJKsc-Black.otf",
        },
    },
    # NushuSerif: not subsetted here.
    # Using official NyushuSerif-1.0022.woff2 (55KB) directly in public/fonts/.
    # Includes 396 nushu + 1765 hanzi double-encoded glyphs + full GSUB.
}


def scan_content(content_dir: str) -> dict[str, set[str]]:
    """Scan all MDX/MD files and collect characters per range."""
    found: dict[str, set[str]] = {name: set() for name in RANGES}

    patterns = ["**/*.mdx", "**/*.md"]
    files = []
    for pat in patterns:
        files.extend(glob.glob(os.path.join(content_dir, pat), recursive=True))

    if not files:
        print(f"  Warning: no content files found in {content_dir}")
        return found

    print(f"  Scanning {len(files)} content files...")

    for filepath in files:
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()
        for char in text:
            cp = ord(char)
            for name, cfg in RANGES.items():
                if cfg["start"] <= cp <= cfg["end"]:
                    found[name].add(char)

    return found


def generate_subset(name: str, weight: int, font_file: str,
                    chars: set[str], output_dir: str) -> None:
    """Generate a woff2 subset for a specific range + weight."""
    source = os.path.join(FONT_DIR, font_file)
    output = os.path.join(output_dir, f"{name}-{weight}.woff2")

    if not os.path.exists(source):
        if weight == 400:
            print(f"  Warning: Source font not found: {source}")
        return

    if not chars:
        if os.path.exists(output):
            os.remove(output)
        return

    from fontTools.subset import Subsetter, Options
    from fontTools.ttLib import TTFont

    options = Options()
    options.flavor = "woff2"
    options.desubroutinize = True
    options.layout_features = []
    options.layout_closure = False
    options.drop_tables += ["meta", "GSUB", "GPOS", "GDEF", "MATH"]

    font = TTFont(source)
    for table in ["GSUB", "GPOS", "GDEF", "MATH"]:
        if table in font:
            del font[table]

    subsetter = Subsetter(options=options)
    subsetter.populate(unicodes=[ord(c) for c in chars])
    subsetter.subset(font)
    font.save(output)
    font.close()

    size = os.path.getsize(output)
    print(f"    {name}-{weight}.woff2 ({size:,} bytes)")


def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <content_dir> <output_dir>")
        sys.exit(1)

    content_dir = sys.argv[1]
    output_dir = sys.argv[2]

    if not os.path.isdir(content_dir):
        print(f"Error: content directory not found: {content_dir}")
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)

    print("Font subsetting for Palimpsestus")
    print("=" * 40)

    found = scan_content(content_dir)

    total = sum(len(v) for v in found.values())
    print(f"  Total rare characters found: {total}")
    print()

    for name, cfg in RANGES.items():
        chars = found[name]
        if not chars:
            print(f"  . {name}: no characters found, skipping")
            continue

        char_display = "".join(sorted(chars))
        print(f"  -> {name}: {len(chars)} chars [{char_display}]")

        generated = 0
        for weight, font_file in sorted(cfg["weights"].items()):
            source = os.path.join(FONT_DIR, font_file)
            if os.path.exists(source):
                generate_subset(name, weight, font_file, chars, output_dir)
                generated += 1

        if generated == 0:
            print(f"    Warning: No source fonts found in {FONT_DIR}")
        else:
            print(f"    Generated {generated} weight variants")

    print()
    print("Done.")


if __name__ == "__main__":
    main()
