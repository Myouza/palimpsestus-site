#!/usr/bin/env python3
"""
subset-fonts.py — Build-time font subsetting for Palimpsestus

Scans all MDX content files, identifies characters outside the coverage
of Google Fonts CDN, and generates minimal woff2 subsets from full source
fonts stored on the server.

Key behavior:
- Generates one woff2 per (range, weight) combination
- Verifies actual glyph coverage before subsetting — chars without real
  glyphs are excluded so browsers can fall through to system fonts
- Reports coverage gaps for debugging

Usage:
    python3 subset-fonts.py <content_dir> <output_dir>

Requires: fonttools, brotli (pip install fonttools brotli)
Source fonts expected at: /opt/palimpsestus/fonts/
"""

import sys
import os
import glob
from pathlib import Path

FONT_DIR = "/opt/palimpsestus/fonts"

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
    # Also cover rare Basic CJK chars that Google Fonts CDN might not
    # serve with all weights. Any char in 4E00-9FFF that appears in
    # content AND exists in our local font will get a local subset.
    # Google Fonts still loads first (it's in the font-family chain),
    # but our local subset acts as a weight-complete fallback.
    "CJKRare-Serif": {
        "start": 0x4E00,
        "end": 0x9FFF,
        "label": "CJK Basic (rare chars)",
        "weights": {
            200: "NotoSerifCJKsc-ExtraLight.otf",
            300: "NotoSerifCJKsc-Light.otf",
            400: "NotoSerifCJKsc-Regular.otf",
            500: "NotoSerifCJKsc-Medium.otf",
            600: "NotoSerifCJKsc-SemiBold.otf",
            700: "NotoSerifCJKsc-Bold.otf",
            900: "NotoSerifCJKsc-Black.otf",
        },
        # Only subset chars that appear in content AND are in a known
        # "rare" list. We don't want to subset all 20,000+ basic CJK.
        "rare_only": True,
    },
    # NushuSerif: not subsetted here.
    # Using official NyushuSerif-1.0022.woff2 (55KB) directly in public/fonts/.
}

# Basic CJK characters known to be rare enough that Google Fonts CDN
# might not serve them with full weight coverage. Add chars here as
# encountered. This is a whitelist — only these chars get local subsets.
RARE_BASIC_CJK = set(
    "迌"  # U+8FCC thô (闽南语)
    "圊"  # U+570A (溷圊)
    "溷"  # U+6E37
)


def check_glyph_coverage(font_path: str, chars: set[str]) -> tuple[set[str], set[str]]:
    """Check which chars have real glyphs (not .notdef) in the font.
    Returns (covered, missing) sets."""
    from fontTools.ttLib import TTFont

    font = TTFont(font_path)
    cmap = font.getBestCmap()
    glyph_set = font.getGlyphOrder()
    notdef = glyph_set[0] if glyph_set else '.notdef'

    covered = set()
    missing = set()

    for char in chars:
        cp = ord(char)
        if cp in cmap:
            glyph_name = cmap[cp]
            # Check it's not mapping to .notdef or an empty glyph
            if glyph_name != notdef and glyph_name != '.notdef':
                covered.add(char)
            else:
                missing.add(char)
        else:
            missing.add(char)

    font.close()
    return covered, missing


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
                    # For rare_only ranges, check whitelist
                    if cfg.get("rare_only") and char not in RARE_BASIC_CJK:
                        continue
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

        # Use the Regular (400) font to check glyph coverage
        regular_file = cfg["weights"].get(400)
        if regular_file:
            regular_path = os.path.join(FONT_DIR, regular_file)
            if os.path.exists(regular_path):
                covered, missing = check_glyph_coverage(regular_path, chars)

                char_display = "".join(sorted(covered))
                print(f"  -> {name}: {len(covered)} chars with glyphs [{char_display}]")

                if missing:
                    miss_display = "".join(sorted(missing))
                    print(f"     {len(missing)} chars WITHOUT glyphs [{miss_display}] (excluded, browser will use system font)")

                # Only subset chars that actually have glyphs
                chars = covered
            else:
                char_display = "".join(sorted(chars))
                print(f"  -> {name}: {len(chars)} chars [{char_display}] (coverage not verified)")

        if not chars:
            print(f"     No chars to subset after coverage check")
            # Clean up any stale files
            for weight in cfg["weights"]:
                stale = os.path.join(output_dir, f"{name}-{weight}.woff2")
                if os.path.exists(stale):
                    os.remove(stale)
            continue

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
