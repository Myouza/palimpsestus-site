#!/usr/bin/env python3
"""
subset-fonts.py — Build-time font subsetting for Palimpsestus

Scans all MDX content files, identifies characters outside the coverage
of Google Fonts CDN (CJK Extension B, Nushu), and generates minimal
woff2 subsets from full source fonts stored on the server.

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
# Configuration: which character ranges need local font coverage
# ---------------------------------------------------------------------------
FONT_DIR = "/opt/palimpsestus/fonts"

RANGES = {
    "CJKExtB-Serif": {
        "source": os.path.join(FONT_DIR, "NotoSerifCJKsc-Regular.otf"),
        "start": 0x20000,
        "end": 0x2A6DF,
        "label": "CJK Extension B",
    },
    "NushuSerif": {
        "source": os.path.join(FONT_DIR, "NyushuFengQi.ttf"),
        "start": 0x1B170,
        "end": 0x1B2FF,
        "label": "Nushu",
    },
}


def scan_content(content_dir: str) -> dict[str, set[str]]:
    """Scan all MDX/MD files and collect characters per font range."""
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


def generate_subset(name: str, chars: set[str], output_dir: str) -> None:
    """Generate a woff2 subset containing only the specified characters."""
    cfg = RANGES[name]
    source = cfg["source"]
    output = os.path.join(output_dir, f"{name}.woff2")

    if not os.path.exists(source):
        print(f"  ⚠ Source font not found: {source}")
        print(f"    Skipping {name} — {cfg['label']} characters will show as fallback")
        return

    if not chars:
        print(f"  · {name}: no characters found, skipping")
        # Remove stale subset if it exists
        if os.path.exists(output):
            os.remove(output)
        return

    # Build unicode list for pyftsubset
    unicodes = ",".join(f"U+{ord(c):04X}" for c in sorted(chars))
    char_display = "".join(sorted(chars))
    print(f"  → {name}: {len(chars)} chars [{char_display}]")

    # Use fonttools programmatically
    from fontTools.subset import Subsetter, Options
    from fontTools.ttLib import TTFont

    options = Options()
    options.flavor = "woff2"
    options.desubroutinize = True
    options.drop_tables += ["meta"]

    font = TTFont(source)
    subsetter = Subsetter(options=options)
    subsetter.populate(unicodes=[ord(c) for c in chars])
    subsetter.subset(font)
    font.save(output)
    font.close()

    size = os.path.getsize(output)
    print(f"    Wrote {output} ({size:,} bytes)")


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

    for name in RANGES:
        generate_subset(name, found[name], output_dir)

    print()
    print("Done.")


if __name__ == "__main__":
    main()
