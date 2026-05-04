#!/usr/bin/env bash

SCRIPT_DIR="$(cd "$(dirname -- "${BASH_SOURCE[0]}")" >/dev/null && pwd)"

git config --global --add safe.directory '*'

set -e -o pipefail

PYTHON="${PYTHON_CMD:-python3}"

${PYTHON} -m pip install --upgrade -r dev-requirements.txt

${PYTHON} -m pip install --force-reinstall qdb/quasardb-*.whl

echo "Invoking pytest"

TEST_OPTS="$@"
if [[ ! -z ${JUNIT_XML_FILE-} ]]
then
    TEST_OPTS+=" --junitxml=${JUNIT_XML_FILE}"
fi

pushd tests
exec ${PYTHON} -m pytest ${TEST_OPTS}
popd

