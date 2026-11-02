#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
BIN="$HOME/.local/bin"
APPS="$HOME/.local/share/applications"
ICONS="$HOME/.local/share/icons/hicolor/scalable/apps"

mkdir -p "$BIN" "$APPS" "$ICONS"
cp "$ROOT/alpine-desktop-center" "$BIN/alpine-desktop-center"
cp "$ROOT/resources/alpine-desktop-center.desktop" "$APPS/alpine-desktop-center.desktop"
cp "$ROOT/resources/alpine-desktop-center.svg" "$ICONS/alpine-desktop-center.svg"
chmod 0755 "$BIN/alpine-desktop-center"

if command -v kbuildsycoca6 >/dev/null 2>&1; then
  kbuildsycoca6 >/dev/null 2>&1 || true
fi

printf '%s\n' 'Alpine Desktop Center installed.'
printf '%s\n' 'Open it from the KDE application menu with two clicks.'
