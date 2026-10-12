#!/usr/bin/env bash
# Build an AppImage from the raw output of `flet build linux`.
#
# Usage: build-appimage.sh <raw-output-path> <version>
set -euo pipefail

RAW_OUTPUT="${1:?raw build output path required}"
VERSION="${2:?version required}"
VERSION_CLEAN="${VERSION#v}"

APP_NAME="GTrans"
ARCH="$(uname -m)"                  # x86_64 on GitHub runners

mkdir -p dist
WORK="$(mktemp -d)"
APPDIR="${WORK}/${APP_NAME}.AppDir"

mkdir -p "${APPDIR}/usr/bin"
mkdir -p "${APPDIR}/usr/share/applications"
mkdir -p "${APPDIR}/usr/share/icons/hicolor/256x256/apps"

# Locate the actual bundle directory containing the gtrans executable.
BUNDLE_DIR="$(dirname "$(find "${RAW_OUTPUT}" -maxdepth 6 -type f -name "gtrans" -perm -u+x | head -n1)")"
if [ -z "${BUNDLE_DIR}" ] || [ ! -d "${BUNDLE_DIR}" ]; then
  echo "Could not locate gtrans executable under ${RAW_OUTPUT}" >&2
  exit 1
fi
echo "Using bundle dir: ${BUNDLE_DIR}"

cp -r "${BUNDLE_DIR}/." "${APPDIR}/usr/bin/"
BIN_NAME="gtrans"

if [ -f "src/assets/icon.png" ]; then
  cp "src/assets/icon.png" \
     "${APPDIR}/usr/share/icons/hicolor/256x256/apps/${BIN_NAME}.png"
  cp "src/assets/icon.png" "${APPDIR}/${BIN_NAME}.png"
fi

cat > "${APPDIR}/${BIN_NAME}.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=${APP_NAME}
Comment=A sophisticated desktop translation companion.
Exec=${BIN_NAME}
Icon=${BIN_NAME}
Terminal=false
Categories=Utility;Education;
EOF
cp "${APPDIR}/${BIN_NAME}.desktop" "${APPDIR}/usr/share/applications/"

cat > "${APPDIR}/AppRun" <<EOF
#!/bin/sh
HERE="\$(dirname "\$(readlink -f "\$0")")"
exec "\${HERE}/usr/bin/${BIN_NAME}" "\$@"
EOF
chmod +x "${APPDIR}/AppRun"

# Fetch appimagetool
APPIMAGETOOL="${WORK}/appimagetool"
curl -sSL -o "${APPIMAGETOOL}" \
  "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-${ARCH}.AppImage"
chmod +x "${APPIMAGETOOL}"

# FUSE is often unavailable on CI runners; --appimage-extract-and-run avoids it.
export ARCH
"${APPIMAGETOOL}" --appimage-extract-and-run "${APPDIR}" \
  "dist/${APP_NAME}-${VERSION_CLEAN}-${ARCH}.AppImage"

echo "Built: dist/${APP_NAME}-${VERSION_CLEAN}-${ARCH}.AppImage"