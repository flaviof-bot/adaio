#!/usr/bin/env bash
set -Eeuo pipefail

BIN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
PROG_DIR="${BIN_DIR%/*}"
TOP_DIR="${PROG_DIR%/*}"

export PYTHONPATH="${PYTHONPATH:-${TOP_DIR}}"

[[ -e /vagrant/.secrets ]] && source /vagrant/.secrets
[[ -e /vagrant/.knobs ]] && source /vagrant/.knobs

cd "${PROG_DIR}"

exec "${TOP_DIR}/env/bin/python" ./main.py "$@"
