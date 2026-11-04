#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

DESKTOP_TEMPLATE="${PROJECT_ROOT}/camera_ui.desktop"
DESKTOP_FILE="${HOME}/Desktop/AstroCam.desktop"

if [ ! -f "${DESKTOP_TEMPLATE}" ]; then
    echo "Desktop template not found:"
    echo "${DESKTOP_TEMPLATE}"
    exit 1
fi

sed \
    -e "s#/home/pi/camera_ui#${PROJECT_ROOT}#g" \
    "${DESKTOP_TEMPLATE}" \
    > "${DESKTOP_FILE}"

chmod +x "${PROJECT_ROOT}/run.py"
chmod +x "${DESKTOP_FILE}"

echo "AstroCam desktop launcher installed:"
echo "${DESKTOP_FILE}"