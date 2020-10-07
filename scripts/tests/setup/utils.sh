#!/bin/bash

set -eux

SCRIPT_DIR="$(cd "$(dirname -- "${BASH_SOURCE[0]}")" >/dev/null && pwd)"
source "$SCRIPT_DIR/binaries.sh"

function qdb_add_user {
    USER_COUNT=1
    local user_list=$1;shift
    local user_private_key=$1;shift
    local username=$1;shift
    ${QDB_USER_ADD} -p ${user_list} -s ${user_private_key} -u ${username} --uid=${USER_COUNT} --superuser=1
    USER_COUNT=$((${USER_COUNT} + 1))
}

function qdb_gen_cluster_keys {
    local public_key=$1;shift
    local private_key=$1;shift
    ${QDB_CLUSTER_KEYGEN} -p ${public_key} -s ${private_key}
}

function qdb_start {
    local args=$1; shift
    local output=$1; shift
    local err_output=$1; shift

    echo "Starting ${QDBD} with args: ${args}"
    echo "Redirecting output to ${output}"
    echo "Redirecting error output to ${err_output}"

    $QDBD ${args} 1>${output} 2>${err_output} &
}

function count_instances {
    local instances_count=$(($(ps aux | grep qdbd | grep -v "grep" | wc -l)))
    echo ${instances_count}
}

function check_address {
    local address=$1;shift
    case "$(uname)" in
        MINGW*)
            local pid=$(NETSTAT.EXE -an -o | grep $address | grep "LISTENING" | tr -s [:space:] | cut -d' ' -f6)
            if [[ $pid != "" ]]; then
                ps aux | grep $pid | grep qdbd
            fi
        ;;
        FreeBSD*)
            sockstat -l | grep $address | tr -s [:space:] | cut -d' ' -f2
        ;;
        *)
            lsof -i -n -P | grep $address | grep LISTEN | cut -d' ' -f1
        ;;
    esac
    echo ""
}

function cluster_wait_for_stabilization {
    local qdbsh_args=$@

    ${QDBSH} ${qdbsh_args} -c "cluster_wait_for_stabilization 30000"
    echo $? # return error code
}

function print_instance_log {
    local log_directory=$1;shift
    local output=$1;shift
    local err_output=$1;shift
    echo "${log_directory}: "
    cat ${log_directory}/* || true

    echo "${output}: "
    cat ${output} || true

    echo "${err_output}: "
    cat ${err_output} || true
}

function kill_instances {
    echo "Killing ${QDBD_FILENAME} instances..."
    case "$(uname)" in
        MINGW*)
            # we need double slashes for the flag to be recognized
            # a simple slash would cause this error: Invalid argument/option - 'C:/Program Files/Git/IM'.
            #
            # See http://www.mingw.org/wiki/Posix_path_conversion
            Taskkill //IM ${QDBD_FILENAME} //F || true
        ;;
        *)
            pkill -SIGKILL -f ${QDBD_FILENAME} || true
        ;;
    esac
    sleep 5
    if [[ $(($(count_instances))) != 0 ]]; then
        echo "Could not kill all instances, aborting..."
        exit 1
    fi
}
