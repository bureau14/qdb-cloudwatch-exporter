#!/bin/bash

set -xe

SCRIPT_DIR="$(cd "$(dirname -- "${BASH_SOURCE[0]}")" >/dev/null && pwd)"
source "$SCRIPT_DIR/config.sh"

function cleanup {
    echo "Removing ${DATA_DIR_INSECURE}..."
    rm -Rf ${DATA_DIR_INSECURE} || true

    echo "Removing ${DATA_DIR_SECURE}..."
    rm -Rf ${DATA_DIR_SECURE} || true

    rm -Rf ${USER_LIST} || true
    rm -Rf ${USER_PRIVATE_KEY} || true
    rm -Rf ${CLUSTER_PUBLIC_KEY} || true
    rm -Rf ${CLUSTER_PRIVATE_KEY} || true
}

function full_cleanup {
    cleanup
    echo "Removing ${LOG_DIR_INSECURE}..."
    rm -Rf ${LOG_DIR_INSECURE} || true
    echo "Removing ${CONSOLE_LOG_INSECURE} ..."
    rm -Rf ${CONSOLE_LOG_INSECURE} || true
    echo "Removing ${CONSOLE_ERR_LOG_INSECURE} ..."
    rm -Rf ${CONSOLE_ERR_LOG_INSECURE} || true

    echo "Removing ${LOG_DIR_SECURE}..."
    rm -Rf ${LOG_DIR_SECURE} || true
    echo "Removing ${CONSOLE_LOG_SECURE} ..."
    rm -Rf ${CONSOLE_LOG_SECURE} || true
    echo "Removing ${CONSOLE_ERR_LOG_SECURE} ..."
    rm -Rf ${CONSOLE_ERR_LOG_SECURE} || true
}
