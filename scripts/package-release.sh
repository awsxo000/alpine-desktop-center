#!/bin/sh
set -eu

FRONTEND_VERSION=${1:-0.1.0-alpha.37}
BACKEND_VERSION=${2:-v1.43}
REPO_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
PACKAGE_NAME="Alpine-Desktop-Center-v${FRONTEND_VERSION}"
BUILD_ROOT=${BUILD_ROOT:-"$REPO_ROOT/dist"}
STAGE="$BUILD_ROOT/$PACKAGE_NAME"
SOURCE_DATE_EPOCH=${SOURCE_DATE_EPOCH:-0}
BACKEND_TMP=$(mktemp -d)
trap 'rm -rf "$BACKEND_TMP"' EXIT HUP INT TERM

rm -rf "$STAGE" "$BUILD_ROOT/$PACKAGE_NAME.tar.gz"
mkdir -p "$STAGE/frontend" "$STAGE/backend"

if [ -n "${BACKEND_SOURCE:-}" ]; then
  echo "Using local backend source ${BACKEND_SOURCE}..."
  [ -d "$BACKEND_SOURCE" ] || { echo "BACKEND_SOURCE must be a directory." >&2; exit 1; }
  cp -R "$BACKEND_SOURCE/." "$BACKEND_TMP/backend/"
else
  echo "Cloning backend ${BACKEND_VERSION}..."
  gh repo clone awsxo000/alpine "$BACKEND_TMP/backend" >/dev/null
  git -C "$BACKEND_TMP/backend" checkout --quiet "$BACKEND_VERSION"
fi
if BACKEND_COMMIT=$(git -C "$BACKEND_TMP/backend" rev-parse HEAD 2>/dev/null); then
  :
else
  BACKEND_COMMIT=${BACKEND_COMMIT_OVERRIDE:-unavailable}
fi
rm -rf "$BACKEND_TMP/backend/.git"

# The source repository stays frontend-only; the release artifact is combined.
cp -R "$REPO_ROOT/CHANGELOG.md" "$REPO_ROOT/CONTRIBUTING.md" "$REPO_ROOT/LICENSE" \
  "$REPO_ROOT/README.md" "$REPO_ROOT/pyproject.toml" "$REPO_ROOT/requirements-dev.txt" \
  "$REPO_ROOT/src" "$REPO_ROOT/resources" "$REPO_ROOT/alpine-desktop-center" \
  "$STAGE/frontend/"
cp -R "$BACKEND_TMP/backend/." "$STAGE/backend/"
cp "$REPO_ROOT/Alpine Desktop Center" "$STAGE/Alpine Desktop Center"
cp "$REPO_ROOT/Alpine Desktop Center.desktop" "$REPO_ROOT/launch-from-desktop.sh" "$STAGE/"
chmod 0755 "$STAGE/Alpine Desktop Center" "$STAGE/launch-from-desktop.sh" "$STAGE/frontend/alpine-desktop-center"

(cd "$STAGE/backend" && find . -type f -print0 | sort -z | xargs -0 sha256sum | sed 's#  \./#  #') > "$STAGE/BACKEND-MANIFEST.sha256"

cat > "$STAGE/RELEASE-VERSIONS" <<EOF
frontend_version=${FRONTEND_VERSION}
backend_version=${BACKEND_VERSION}
backend_commit=${BACKEND_COMMIT}
diagnostic_schema=1
EOF

cat > "$STAGE/README-RELEASE.txt" <<EOF
Alpine Desktop Center ${FRONTEND_VERSION}

This is a self-contained release. The frontend uses only the backend in ./backend.
Do not remove or replace the backend directory.

Frontend: ${FRONTEND_VERSION}
Backend: ${BACKEND_VERSION}
Backend commit: ${BACKEND_COMMIT}

Launch with:
  ./Alpine Desktop Center
EOF

mkdir -p "$BUILD_ROOT"
find "$STAGE" -exec touch -h -d "@$SOURCE_DATE_EPOCH" {} +
tar -C "$BUILD_ROOT" --sort=name --owner=0 --group=0 --numeric-owner \
  --mtime="@$SOURCE_DATE_EPOCH" -cf - "$PACKAGE_NAME" | gzip -n > "$BUILD_ROOT/$PACKAGE_NAME.tar.gz"
printf '%s\n' "$BUILD_ROOT/$PACKAGE_NAME.tar.gz"
