#!/usr/bin/env bash
# Build a .deb from the raw output of `flet build linux`.
#
# Usage: build-deb.sh <raw-output-path> <version>
set -euo pipefail

RAW_OUTPUT="${1:?raw build output path required}"
VERSION="${2:?version required}"
VERSION_CLEAN="${VERSION#v}"

PKG_NAME="gtrans"
ARCH="$(dpkg --print-architecture)"     # amd64 on GitHub runners
WORK="$(mktemp -d)"
PKG_DIR="${WORK}/${PKG_NAME}_${VERSION_CLEAN}_${ARCH}"

mkdir -p dist
mkdir -p "${PKG_DIR}/DEBIAN"
mkdir -p "${PKG_DIR}/usr/bin"
mkdir -p "${PKG_DIR}/usr/share/applications"
mkdir -p "${PKG_DIR}/usr/share/icons/hicolor/256x256/apps"

# The raw flet output may be the bundle itself or a parent directory.
# Find the directory that contains the gtrans executable.
BUNDLE_DIR="$(dirname "$(find "${RAW_OUTPUT}" -maxdepth 6 -type f -name "${PKG_NAME}" -perm -u+x | head -n1)")"
if [ -z "${BUNDLE_DIR}" ] || [ ! -d "${BUNDLE_DIR}" ]; then
  echo "Could not locate '${PKG_NAME}' executable under ${RAW_OUTPUT}" >&2
  exit 1
fi
echo "Using bundle dir: ${BUNDLE_DIR}"

cp -r "${BUNDLE_DIR}/." "${PKG_DIR}/usr/bin/"

if [ -f "src/assets/icon.png" ]; then
  cp "src/assets/icon.png" \
     "${PKG_DIR}/usr/share/icons/hicolor/256x256/apps/${PKG_NAME}.png"
fi

cat > "${PKG_DIR}/usr/share/applications/${PKG_NAME}.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=GTrans
Comment=A sophisticated desktop translation companion.
Exec=${PKG_NAME}
Icon=${PKG_NAME}
Terminal=false
Categories=Utility;Education;
EOF

INSTALLED_SIZE=$(du -sk "${PKG_DIR}/usr" | cut -f1)
cat > "${PKG_DIR}/DEBIAN/control" <<EOF
Package: ${PKG_NAME}
Version: ${VERSION_CLEAN}
Section: utils
Priority: optional
Architecture: ${ARCH}
Installed-Size: ${INSTALLED_SIZE}
Maintainer: Osama Mohammed <support.osamalzabidi@gmail.com>
Description: A sophisticated desktop translation companion.
EOF

dpkg-deb --build --root-owner-group "${PKG_DIR}" \
  "dist/${PKG_NAME}_${VERSION_CLEAN}_${ARCH}.deb"

echo "Built: dist/${PKG_NAME}_${VERSION_CLEAN}_${ARCH}.deb"