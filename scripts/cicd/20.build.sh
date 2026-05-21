#!/usr/bin/env bash

SCRIPT_DIR="$(cd "$(dirname -- "${BASH_SOURCE[0]}")" >/dev/null && pwd)"

git config --global --add safe.directory '*'

set -e -o pipefail

PYTHON="${PYTHON_CMD:-python3}"

if [[ -d "dist/" ]]
then
    echo "Removing dist/"
    rm -rf dist/
fi

${PYTHON} -m pip install --upgrade -r dev-requirements.txt

${PYTHON} -m pip install --force-reinstall qdb/quasardb-*.whl

echo "Building wheel"

${PYTHON} setup.py bdist_wheel
