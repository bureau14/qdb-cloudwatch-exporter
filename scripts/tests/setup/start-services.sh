#!/bin/bash

set -ex

echo "QDB_ENABLE_SECURE_CLUSTER=${QDB_ENABLE_SECURE_CLUSTER:=1}"

set -u

SCRIPT_DIR="$(cd "$(dirname -- "${BASH_SOURCE[0]}")" >/dev/null && pwd)"
source "$SCRIPT_DIR/config.sh" $@ # important: pass $@ as config.sh also parses our runtime args
source "$SCRIPT_DIR/utils.sh"
source "$SCRIPT_DIR/cleanup.sh"

kill_instances
full_cleanup
check_binaries

qdb_add_user ${USER_LIST} ${USER_PRIVATE_KEY} "test-user"
qdb_gen_cluster_keys ${CLUSTER_PUBLIC_KEY} ${CLUSTER_PRIVATE_KEY}

# This whole iteration is mostly unnecessary in case there's just a single-node
# cluster (the common case), but sometimes we want to launch a cluster.
#
# In this case, we want to assign specific node ids to each node in the cluster.
# Each of them also is listening on a unique port.
#
# The clusters will end up looking like this:
#
# - port 2836, cluster insecure, node 1
# - port 2838, cluster secure, node 1
# - port 2840, cluster insecure, node 2
# - port 2842, cluster secure, node 2
# .. etc
#
# We are all providing the 'base' configuration qdbd.conf (if provided), and override
# the address etc using the `-a` `--id` flags.
COUNT=0
for NODE_ID in "${NODE_IDS[@]}"
do
    # Magic number 4, as we need 4 ports per secure/insecure "pair"
    PORT_INSECURE=$((2836 + ($COUNT * 4)))
    PORT_SECURE=$((2838 + ($COUNT * 4)))

    THIS_DATA_DIR_INSECURE="${DATA_DIR_INSECURE}/${NODE_ID}"
    THIS_LOG_DIR_INSECURE="${LOG_DIR_INSECURE}/${NODE_ID}"
    THIS_DATA_DIR_SECURE="${DATA_DIR_SECURE}/${NODE_ID}"
    THIS_LOG_DIR_SECURE="${LOG_DIR_SECURE}/${NODE_ID}"

    # Ensure directories exist
    mkdir -p ${THIS_DATA_DIR_INSECURE} || true
    mkdir -p ${THIS_LOG_DIR_INSECURE} || true
    mkdir -p ${THIS_DATA_DIR_SECURE} || true
    mkdir -p ${THIS_LOG_DIR_SECURE} || true

    THIS_URI_INSECURE="127.0.0.1:${PORT_INSECURE}"
    THIS_URI_SECURE="127.0.0.1:${PORT_SECURE}"

    echo "Cluster insecure:"
    ARGS_INSECURE="--id ${NODE_ID} -a ${THIS_URI_INSECURE} -r ${THIS_DATA_DIR_INSECURE} -l ${THIS_LOG_DIR_INSECURE} --enable-performance-profiling --with-firehose \$qdb.firehose"
    if [[ -f ${CONFIG_INSECURE} ]]; then
        ARGS_INSECURE="${ARGS_INSECURE} -c ${CONFIG_INSECURE}"
    fi

    if [[ "$COUNT" != "0" ]]
    then
        # Not the first node, which means we need to bootstrap using the previous node
        BOOTSTRAP_PORT_INSECURE=$((2836 + (($COUNT - 1) * 4)))
        BOOTSTRAP_URI_INSECURE="127.0.0.1:${BOOTSTRAP_PORT_INSECURE}"
        ARGS_INSECURE="${ARGS_INSECURE} --peer ${BOOTSTRAP_URI_INSECURE}"
    fi

    qdb_start "${ARGS_INSECURE}" ${CONSOLE_LOG_INSECURE} ${CONSOLE_ERR_LOG_INSECURE}

    if [ ${QDB_ENABLE_SECURE_CLUSTER} -ne 0 ] ; then
        echo "Cluster secure:"
        ARGS_SECURE="--id ${NODE_ID} -a ${THIS_URI_SECURE} -r ${THIS_DATA_DIR_SECURE} -l ${THIS_LOG_DIR_SECURE} --enable-performance-profiling  --with-firehose \$qdb.firehose --security=true --cluster-private-file=${CLUSTER_PRIVATE_KEY} --user-list=${USER_LIST}"
        if [[ -f ${CONFIG_SECURE} ]]; then
            ARGS_SECURE="${ARGS_SECURE} -c ${CONFIG_SECURE}"
        fi
        qdb_start "${ARGS_SECURE}" ${CONSOLE_LOG_SECURE} ${CONSOLE_ERR_LOG_SECURE}
    fi

    COUNT=$((COUNT + 1))

done

sleep_time=5
timeout=60
end_time=$(($(date +%s) + $timeout))
SUCCESS=0
while [ $(date +%s) -le $end_time ]; do
    insecure_check=$(check_address $URI_INSECURE)
    if [ ${QDB_ENABLE_SECURE_CLUSTER} -ne 0 ] ; then
        secure_check=$(check_address $URI_SECURE)
    else
        secure_check="OK"
    fi

    if [[ $insecure_check != "" && $secure_check != "" ]]; then
        echo "qdbd secure and insecure were started properly."
        SUCCESS=1
        break
    fi

    sleep $sleep_time
done

if [[ "${SUCCESS}" == "0" ]]
then
    echo "Could not start all instances, aborting..."
    exit 1
fi

if [[ ${#NODE_IDS[@]} -gt 1 ]]
then
    SUCCESS=0
    # Clustered setup, wait for stabilization
    end_time=$(($(date +%s) + $timeout))
    timeout=300 # stabilization can take a long time!
    sleep_time=5
    while [ $(date +%s) -le $end_time ]
    do
        # HACKS(leon): THIS_URI_INSECURE and THIS_URI_SECURE are extremely hacky
        # as they are the last set URIs for the cluster's node in the loop above..
        #
        # A better way to approach this is to build some utility functions for resolving
        # node URIs... perhaps even initialize all these things in config.sh?
        insecure_check=$(cluster_wait_for_stabilization \
                             --cluster qdb://${THIS_URI_INSECURE})
        if [ ${QDB_ENABLE_SECURE_CLUSTER} -ne 0 ] ; then
            secure_check=$(cluster_wait_for_stabilization \
                               --cluster qdb://${THIS_URI_SECURE} \
                               --cluster-public-key ${CLUSTER_PUBLIC_KEY} \
                               --user-security-file ${USER_PRIVATE_KEY})
        else
            secure_check="0"
        fi

        if [[ "${insecure_check}" == "0" && "${secure_check}" == "0" ]]
        then
            echo "both clusters stable!"
            SUCCESS=1
            break
        fi

        echo "Not all clusters are stable, sleeping for ${sleep_time}s before retry.."
        sleep $sleep_time
    done

    if [[ "${SUCCESS}" == "0" ]]
    then
        echo "Cluster did not become stable, abort!"
        exit 1
    fi
fi
