#!/usr/bin/env bash
# server-deploy.sh — Server-side build & deploy for Palimpsestus
#
# Called by GitHub Actions via SSH. Handles:
#   1. Pull latest code from both repos
#   2. Merge content into framework
#   3. Run font subsetting (scan content → generate woff2 from server fonts)
#   4. Build with Astro
#   5. Deploy to web root
#
# Usage:
#   ./server-deploy.sh <content_branch> <framework_branch>
#
# Examples:
#   ./server-deploy.sh main main          # Production deploy
#   ./server-deploy.sh preview main       # Content preview
#   ./server-deploy.sh main preview       # Framework preview (rare)
#   ./server-deploy.sh preview preview    # Full preview

set -euo pipefail

# ── Configuration ──────────────────────────────────────────
PALIMPSESTUS_ROOT="/opt/palimpsestus"
FRAMEWORK_REPO="$PALIMPSESTUS_ROOT/repos/framework"
CONTENT_REPO="$PALIMPSESTUS_ROOT/repos/content"
FONT_DIR="$PALIMPSESTUS_ROOT/fonts"
VENV_PYTHON="$PALIMPSESTUS_ROOT/venv/bin/python3"
WEB_ROOT="/var/www"

# ── Arguments ──────────────────────────────────────────────
CONTENT_BRANCH="${1:?Usage: $0 <content_branch> <framework_branch>}"
FRAMEWORK_BRANCH="${2:-main}"

# Determine deploy target
if [ "$CONTENT_BRANCH" = "main" ] && [ "$FRAMEWORK_BRANCH" = "main" ]; then
    DEPLOY_TARGET="production"
else
    DEPLOY_TARGET="staging"
fi

DEPLOY_DIR="$WEB_ROOT/$DEPLOY_TARGET"

echo "╔══════════════════════════════════════════╗"
echo "║  Palimpsestus Deploy                     ║"
echo "╚══════════════════════════════════════════╝"
echo "  Framework: $FRAMEWORK_BRANCH"
echo "  Content:   $CONTENT_BRANCH"
echo "  Target:    $DEPLOY_TARGET → $DEPLOY_DIR"
echo ""

# ── Load nvm (non-interactive shell) ───────────────────────
export NVM_DIR="$HOME/.nvm"
if [ -s "$NVM_DIR/nvm.sh" ]; then
    source "$NVM_DIR/nvm.sh"
    echo "✓ nvm loaded (Node $(node -v))"
else
    echo "✗ nvm not found at $NVM_DIR/nvm.sh"
    exit 1
fi

# ── Verify prerequisites ──────────────────────────────────
[ -x "$VENV_PYTHON" ] || { echo "✗ venv python not found at $VENV_PYTHON"; exit 1; }
$VENV_PYTHON -c "import fontTools" 2>/dev/null || { echo "✗ fonttools not installed in venv"; exit 1; }
echo "✓ Prerequisites verified"
echo ""

# ── Pull framework repo ───────────────────────────────────
echo "── Pulling framework ($FRAMEWORK_BRANCH) ──"
cd "$FRAMEWORK_REPO"
git fetch origin
git checkout "$FRAMEWORK_BRANCH"
git reset --hard "origin/$FRAMEWORK_BRANCH"
echo "  ✓ framework @ $(git rev-parse --short HEAD) ($(git branch --show-current))"
echo ""

# ── Pull content repo ─────────────────────────────────────
echo "── Pulling content ($CONTENT_BRANCH) ──"
cd "$CONTENT_REPO"
git fetch origin
git checkout "$CONTENT_BRANCH"
git reset --hard "origin/$CONTENT_BRANCH"
echo "  ✓ content @ $(git rev-parse --short HEAD) ($(git branch --show-current))"
echo ""

# ── Merge content into framework ──────────────────────────
echo "── Merging content ──"
cd "$FRAMEWORK_REPO"
rm -rf src/content/novel
mkdir -p src/content/novel
cp -r "$CONTENT_REPO"/[0-9]*/ src/content/novel/ 2>/dev/null || true
find src/content/novel -name 'meta.yaml' -delete
if [ -d "$CONTENT_REPO/assets" ]; then
    cp -r "$CONTENT_REPO/assets/" public/assets/
fi
CONTENT_COUNT=$(find src/content/novel -name '*.mdx' | wc -l)
echo "  Content files: $CONTENT_COUNT mdx files from $CONTENT_BRANCH"
find src/content/novel -name '*.mdx' | sort | sed 's/^/    /'
echo ""

# ── Font subsetting ───────────────────────────────────────
echo "── Subsetting fonts ──"
$VENV_PYTHON scripts/subset-fonts.py src/content/novel public/fonts
echo ""

# ── Install dependencies ──────────────────────────────────
echo "── Installing dependencies ──"
npm ci --prefer-offline 2>&1 | tail -1
echo ""

# ── Build ─────────────────────────────────────────────────
echo "── Building site ──"
npm run build 2>&1 | tail -5
echo ""

# ── Deploy ────────────────────────────────────────────────
echo "── Deploying to $DEPLOY_DIR ──"
mkdir -p "$DEPLOY_DIR"
rsync -a --delete dist/ "$DEPLOY_DIR/"
echo "✓ Deployed $(find dist -name '*.html' | wc -l) pages"
echo ""

echo "╔══════════════════════════════════════════╗"
echo "║  ✓ Deploy complete: $DEPLOY_TARGET       "
echo "╚══════════════════════════════════════════╝"
