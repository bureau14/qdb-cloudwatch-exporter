#!/usr/bin/env bash

set -eux

# For flexibility, we accept $1 to be a path to the qdb license generator,
# or use the one found in path by default.
LICENSE_GEN=${1-qdb_license_gen}

OUTPUT_FILE=${2-license.key}

${LICENSE_GEN} --no-confirmation \
               --company-name QuasarDB \
               --email noreply@quasardb.net \
               --max-memory 1024 \
               --support-until 2030-01-01 \
               --expiration-date 2030-01-01 \
               --output-file ${OUTPUT_FILE}
