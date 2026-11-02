#!/bin/sh
set -eu

FRONTEND_VERSION=${1:-0.1.0-alpha.25}
BACKEND_VERSION=${2:-v1.37}
REPO_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
PACKAGE_NAME="Alpine-Desktop-Center-v${FRONTEND_VERSION}"
BUILD_ROOT=${BUILD_ROOT:-"$REPO_ROOT/dist"}
STAGE="$BUILD_ROOT/$PACKAGE_NAME"
BACKEND_TMP=$(mktemp -d)
trap 'rm -rf "$BACKEND_TMP"' EXIT HUP INT TERM

rm -rf "$STAGE" "$BUILD_ROOT/$PACKAGE_NAME.tar.gz"
mkdir -p "$STAGE/frontend" "$STAGE/backend"

echo "Cloning backend ${BACKEND_VERSION}..."
gh repo clone awsxo000/alpine "$BACKEND_TMP/backend" >/dev/null
git -C "$BACKEND_TMP/backend" checkout --quiet "$BACKEND_VERSION"
BACKEND_COMMIT=$(git -C "$BACKEND_TMP/backend" rev-parse HEAD)
rm -rf "$BACKEND_TMP/backend/.git"

# The source repository stays frontend-only; the release artifact is combined.
cp -R "$REPO_ROOT/CHANGELOG.md" "$REPO_ROOT/CONTRIBUTING.md" "$REPO_ROOT/LICENSE" \
  "$REPO_ROOT/README.md" "$REPO_ROOT/pyproject.toml" "$REPO_ROOT/requirements-dev.txt" \
  "$REPO_ROOT/src" "$REPO_ROOT/resources" "$REPO_ROOT/alpine-desktop-center" \
  "$STAGE/frontend/"
cp -R "$BACKEND_TMP/backend/." "$STAGE/backend/"
cp "$REPO_ROOT/Alpine Desktop Center" "$STAGE/Alpine Desktop Center"
chmod 0755 "$STAGE/Alpine Desktop Center" "$STAGE/frontend/alpine-desktop-center"

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
tar -C "$BUILD_ROOT" -czf "$BUILD_ROOT/$PACKAGE_NAME.tar.gz" "$PACKAGE_NAME"
printf '%s\n' "$BUILD_ROOT/$PACKAGE_NAME.tar.gz"
