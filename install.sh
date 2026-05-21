#!/bin/bash
set -euo pipefail

# d-skill-forge installer
# Usage: curl -fsSL https://raw.githubusercontent.com/d-init-d/d-skill-forge/main/install.sh | bash

REPO="d-init-d/d-skill-forge"
BINARY="dskillforge"
INSTALL_DIR="${INSTALL_DIR:-/usr/local/bin}"

# Detect OS and arch
OS="$(uname -s | tr '[:upper:]' '[:lower:]')"
ARCH="$(uname -m)"

case "$OS" in
  linux)  ASSET="dskillforge-linux-amd64" ;;
  darwin) ASSET="dskillforge-darwin-amd64" ;;
  *)      echo "❌ Unsupported OS: $OS"; exit 1 ;;
esac

case "$ARCH" in
  x86_64|amd64) ;; # already set above
  arm64|aarch64) ASSET="${ASSET/amd64/arm64}" ;;
  *) echo "❌ Unsupported architecture: $ARCH"; exit 1 ;;
esac

# Get latest release tag
echo "🔍 Finding latest release..."
TAG=$(curl -fsSL "https://api.github.com/repos/$REPO/releases/latest" | grep '"tag_name"' | cut -d'"' -f4)

if [ -z "$TAG" ]; then
  echo "❌ Could not find latest release"
  exit 1
fi

echo "📦 Downloading $BINARY $TAG for $OS/$ARCH..."
URL="https://github.com/$REPO/releases/download/$TAG/$ASSET"

# Download
TMPFILE=$(mktemp)
curl -fsSL "$URL" -o "$TMPFILE"
chmod +x "$TMPFILE"

# Install
if [ -w "$INSTALL_DIR" ]; then
  mv "$TMPFILE" "$INSTALL_DIR/$BINARY"
else
  echo "📝 Need sudo to install to $INSTALL_DIR"
  sudo mv "$TMPFILE" "$INSTALL_DIR/$BINARY"
fi

echo ""
echo "✅ $BINARY $TAG installed to $INSTALL_DIR/$BINARY"
echo ""
echo "   Run: dskillforge"
echo ""
