#!/bin/bash
set -euo pipefail

# ============================================================
# CulminationAI Workflow — Bootstrap Installer
#
# Usage:
#   curl -sL https://raw.githubusercontent.com/culminationAI/culminationWorkFlow/main/install.sh | bash
#   # OR
#   bash install.sh
# ============================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ok()   { echo -e "${GREEN}[OK]${NC} $1"; }
warn() { echo -e "${YELLOW}[!!]${NC} $1"; }
fail() { echo -e "${RED}[FAIL]${NC} $1"; exit 1; }

REPO="https://github.com/culminationAI/culminationWorkFlow.git"
TARGET_DIR="$(pwd)"

echo "================================================"
echo "  CulminationAI Workflow Installer"
echo "  Target: $TARGET_DIR"
echo "================================================"

# Check git
command -v git >/dev/null 2>&1 || fail "git not found"

# Clone to temp dir
TMPDIR=$(mktemp -d)
trap "rm -rf $TMPDIR" EXIT

echo "Downloading workflow..."
git clone --depth 1 "$REPO" "$TMPDIR/workflow" 2>/dev/null || fail "Failed to clone repo"
ok "Downloaded"

# Copy workflow files (don't overwrite existing)
echo "Installing files..."

# Core directories
for dir in .claude protocols memory mcp infra secrets; do
  if [ ! -d "$TARGET_DIR/$dir" ]; then
    cp -r "$TMPDIR/workflow/$dir" "$TARGET_DIR/$dir"
    ok "$dir/"
  else
    warn "$dir/ already exists — skipping"
  fi
done

# Setup script
if [ ! -f "$TARGET_DIR/setup.sh" ]; then
  cp "$TMPDIR/workflow/setup.sh" "$TARGET_DIR/setup.sh"
  chmod +x "$TARGET_DIR/setup.sh"
  ok "setup.sh"
else
  warn "setup.sh already exists — skipping"
fi

# Single files
for file in CLAUDE.md user-identity.md; do
  if [ ! -f "$TARGET_DIR/$file" ]; then
    cp "$TMPDIR/workflow/$file" "$TARGET_DIR/$file"
    ok "$file"
  else
    warn "$file already exists — skipping"
  fi
done

echo ""
echo "================================================"
echo -e "  ${GREEN}Workflow installed!${NC}"
echo "================================================"
echo ""
echo "Next steps:"
echo "  1. Run: ./setup.sh --check    (verify prerequisites)"
echo "  2. Run: ./setup.sh            (deploy infrastructure)"
echo "  3. Open this directory in Claude Code"
echo "  4. Claude will auto-detect the workflow and guide you through initialization"
echo ""
