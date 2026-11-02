#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
BIN="$HOME/.local/bin"
APPS="$HOME/.local/share/applications"

mkdir -p "$BIN" "$APPS"
cp "$ROOT/alpine-desktop-center" "$BIN/alpine-desktop-center"
cp "$ROOT/resources/alpine-desktop-center.desktop" "$APPS/alpine-desktop-center.desktop"
chmod 0755 "$BIN/alpine-desktop-center"

if command -v kbuildsycoca6 >/dev/null 2>&1; then
  kbuildsycoca6 >/dev/null 2>&1 || true
fi

printf '%s\n' 'Alpine Desktop Center installed.'
printf '%s\n' 'Open it from the KDE application menu with two clicks.'
