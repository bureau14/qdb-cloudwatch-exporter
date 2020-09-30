#!/bin/bash

set -xe

if [[ -z ${QDB_DIR+set} ]]; then
    QDB_DIR="qdb/bin"
    echo "Setting QDB_DIR to ${QDB_DIR}"
fi

if [[ ! -d ${QDB_DIR} ]]; then
    echo "Please provide a valid binary directory, got: ${QDB_DIR}"
    exit 1
fi

QDBD="${QDB_DIR}/qdbd"
QDBSH="${QDB_DIR}/qdbsh"
QDB_USER_ADD="${QDB_DIR}/qdb_user_add"
QDB_CLUSTER_KEYGEN="${QDB_DIR}/qdb_cluster_keygen"

set +u

BINARIES=(QDBD QDBSH QDB_USER_ADD QDB_CLUSTER_KEYGEN)

if [[ ${CMAKE_BUILD_TYPE} == "Debug" ]]; then
    for binary in ${BINARIES[@]} ; do
        declare "${binary}"="${!binary}d"
    done
fi

set -u

case "$(uname)" in
    MINGW*)
        for binary in ${BINARIES[@]} ; do
            declare "${binary}"="${!binary}.exe"
        done
    ;;
    *)
    ;;
esac

for binary in ${BINARIES[@]} ; do
    echo "${binary}"="${!binary}"
done

QDBD_FILENAME=${QDBD##*/}

function check_binary {
    local binary=$1;shift

    if [[ ! -f ${binary} ]]; then
        echo "Binary ${binary} not found."
        return 1
    fi
    return 0
}

function check_binaries {
    FOUND=0

    set +e
    for binary in ${BINARIES[@]} ; do
        if ! check_binary "${!binary}" ; then
            FOUND=1
        fi
    done
    set -e

    if [[ ${FOUND} != 0 ]] ; then
        echo "Binaries not found. Exiting..."
        exit 1
    fi
}
