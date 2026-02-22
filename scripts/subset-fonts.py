#!/usr/bin/env python3
"""
subset-fonts.py — Full-site font subsetting for Palimpsestus

Scans all content files, extracts every unique character, and generates
woff2 subsets from the full Noto Serif CJK SC source fonts on the server.

This replaces Google Fonts CDN entirely. All characters — common and rare,
basic CJK and extension blocks — come from the same source fonts, ensuring
pixel-perfect visual consistency across all platforms.

Only the three weights actually used by CSS are generated:
  400 (body text), 600 (headings), 700 (bold/strong)

Usage:
    python3 subset-fonts.py <content_dir> <output_dir>

Requires: fonttools, brotli (pip install fonttools brotli)
Source fonts: /opt/palimpsestus/fonts/NotoSerifCJKsc-*.otf
"""

import sys
import os
import glob

FONT_DIR = "/opt/palimpsestus/fonts"

# Only the weights our CSS actually uses.
# Maps CSS font-weight → source OTF filename.
WEIGHTS = {
    400: "NotoSerifCJKsc-Regular.otf",
    600: "NotoSerifCJKsc-SemiBold.otf",
    700: "NotoSerifCJKsc-Bold.otf",
}

# Characters to always include even if not in content files.
# Covers common punctuation and symbols that might appear dynamically
# (e.g. via JavaScript, page navigation, etc.)
ALWAYS_INCLUDE = set(
    "…—–·「」『』（）《》〈〉【】""''！？。，、；：" 
    "abcdefghijklmnopqrstuvwxyz"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789"
    " !\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~"
    "←→↑↓"
    "✉·›"
)

# Output font-family name used in CSS
FAMILY = "SiteSerif"


def scan_content(content_dir: str) -> set[str]:
    """Scan all MDX/MD files and collect every unique character."""
    chars = set()

    patterns = ["**/*.mdx", "**/*.md"]
    files = []
    for pat in patterns:
        files.extend(glob.glob(os.path.join(content_dir, pat), recursive=True))

    if not files:
        print(f"  Warning: no content files found in {content_dir}")
        return chars

    print(f"  Scanning {len(files)} content files...")

    for filepath in files:
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()
        chars.update(text)

    # Add guaranteed characters
    chars.update(ALWAYS_INCLUDE)

    # Remove control characters (keep only printable)
    chars = {c for c in chars if ord(c) >= 0x20}

    return chars


def check_coverage(font_path: str, chars: set[str]) -> tuple[set[str], set[str]]:
    """Check which chars have real glyphs in the font."""
    from fontTools.ttLib import TTFont

    font = TTFont(font_path)
    cmap = font.getBestCmap()
    glyph_order = font.getGlyphOrder()
    notdef = glyph_order[0] if glyph_order else '.notdef'

    covered = set()
    missing = set()

    for char in chars:
        cp = ord(char)
        if cp in cmap and cmap[cp] != notdef and cmap[cp] != '.notdef':
            covered.add(char)
        else:
            missing.add(char)

    font.close()
    return covered, missing


def generate_subset(weight: int, font_file: str, chars: set[str],
                    output_dir: str) -> int:
    """Generate a woff2 subset. Returns file size or 0 on failure."""
    source = os.path.join(FONT_DIR, font_file)
    output = os.path.join(output_dir, f"{FAMILY}-{weight}.woff2")

    if not os.path.exists(source):
        print(f"    Warning: {source} not found, skipping weight {weight}")
        return 0

    from fontTools.subset import Subsetter, Options
    from fontTools.ttLib import TTFont

    options = Options()
    options.flavor = "woff2"
    options.desubroutinize = True
    # Keep basic layout features for proper rendering
    options.layout_features = ['kern', 'liga', 'calt', 'ccmp', 'locl']
    options.drop_tables += ["meta", "MATH"]

    font = TTFont(source)

    subsetter = Subsetter(options=options)
    subsetter.populate(unicodes=[ord(c) for c in chars])
    subsetter.subset(font)
    font.save(output)
    font.close()

    size = os.path.getsize(output)
    return size


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

    # Step 1: Scan content
    all_chars = scan_content(content_dir)
    print(f"  Total unique characters: {len(all_chars)}")

    # Step 2: Check coverage against Regular weight
    regular_path = os.path.join(FONT_DIR, WEIGHTS[400])
    if not os.path.exists(regular_path):
        print(f"  Error: {regular_path} not found!")
        sys.exit(1)

    covered, missing = check_coverage(regular_path, all_chars)

    # Categorize for reporting
    cjk_covered = {c for c in covered if ord(c) >= 0x4E00}
    latin_covered = {c for c in covered if ord(c) < 0x4E00}
    cjk_missing = {c for c in missing if ord(c) >= 0x2000}  # non-trivial missing

    print(f"  Covered by font: {len(covered)} ({len(cjk_covered)} CJK + {len(latin_covered)} Latin/symbols)")
    if cjk_missing:
        miss_display = "".join(sorted(cjk_missing)[:20])
        extra = f" (+{len(cjk_missing)-20} more)" if len(cjk_missing) > 20 else ""
        print(f"  CJK chars without glyphs: {len(cjk_missing)} [{miss_display}]{extra}")
        print(f"    (these will fall back to system fonts)")
    print()

    # Step 3: Generate subsets for each weight
    print(f"  Generating {len(WEIGHTS)} weight variants...")
    total_size = 0
    for weight, font_file in sorted(WEIGHTS.items()):
        size = generate_subset(weight, font_file, covered, output_dir)
        if size > 0:
            total_size += size
            print(f"    {FAMILY}-{weight}.woff2  ({size:,} bytes)")

    # Clean up old files from previous architecture
    for old_pattern in ["CJKExtB-Serif-*.woff2", "CJKRare-Serif-*.woff2"]:
        for old_file in glob.glob(os.path.join(output_dir, old_pattern)):
            os.remove(old_file)
            print(f"    Cleaned up old file: {os.path.basename(old_file)}")

    print()
    print(f"  Total font size: {total_size:,} bytes ({total_size/1024:.0f} KB)")
    print("Done.")


if __name__ == "__main__":
    main()
