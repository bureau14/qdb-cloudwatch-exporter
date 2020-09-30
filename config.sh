#!/bin/bash

set -xe

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# Static config

USER_LIST="users.cfg"
USER_PRIVATE_KEY="user_private.key"
CLUSTER_PUBLIC_KEY="cluster_public.key"
CLUSTER_PRIVATE_KEY="cluster_private.key"

DATA_DIR_INSECURE="insecure/db"
LOG_DIR_INSECURE="insecure/log"
URI_INSECURE="127.0.0.1:2836"
CONFIG_INSECURE="${SCRIPT_DIR}/default.qdbd.cfg"
CONSOLE_LOG_INSECURE="qdbd_log_insecure.out.txt"
CONSOLE_ERR_LOG_INSECURE="qdbd_log_insecure.err.txt"

DATA_DIR_SECURE="secure/db"
LOG_DIR_SECURE="secure/log"
URI_SECURE="127.0.0.1:2838"
CONFIG_SECURE="${SCRIPT_DIR}/default.qdbd.cfg"
CONSOLE_LOG_SECURE="qdbd_log_secure.out.txt"
CONSOLE_ERR_LOG_SECURE="qdbd_log_secure.err.txt"

DATA_DIR_INSECURE="insecure/db"
LOG_DIR_INSECURE="insecure/log"
URI_INSECURE="127.0.0.1:2836"
CONSOLE_LOG_INSECURE="qdbd_log_insecure.out.txt"
CONSOLE_ERR_LOG_INSECURE="qdbd_log_insecure.err.txt"

LICENSE_FILE="license.key"

# Runtime configuration, parse arguments
NODE_IDS=("0-0-0-1")

# StackOverflow-driven development
# - https://stackoverflow.com/a/14203146
while [[ $# -gt 0 ]]
do
    key="$1"

    case $key in
        -i|--node-ids)
            # Node IDS are a comma-separated list
            IFS=', ' read -r -a NODE_IDS <<< "$2"
            shift # past argument
            shift # past value
            ;;
    esac
done
