#!/bin/sh
set -eu

DESKTOP_FILE=${1:-}
case "$DESKTOP_FILE" in
  file://*) DESKTOP_FILE=${DESKTOP_FILE#file://} ;;
esac

if [ -z "$DESKTOP_FILE" ] || [ ! -f "$DESKTOP_FILE" ]; then
  printf '%s\n' 'Could not determine the location of Alpine Desktop Center.desktop.' >&2
  exit 1
fi

APP_DIR=$(CDPATH= cd -- "$(dirname -- "$DESKTOP_FILE")" && pwd)
exec "$APP_DIR/alpine-desktop-center" "$@"
