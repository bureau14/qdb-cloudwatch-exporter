import copy
import json
import logging
import random
import re
import uuid

import quasardb
import quasardb.stats as qdbst

logger = logging.getLogger(__name__)


def _slurp(x):
    with open(x, "r") as fp:
        return fp.read()


def _parse_user_security_file(x):
    with open(x, "r") as fp:
        parsed = json.load(fp)
        return (parsed["username"], parsed["secret_key"])


def get_qdb_conn(uri, cluster_public_key=None, user_security_file=None):
    logger.info("Getting qdb connection")
    if cluster_public_key and user_security_file:
        user, private_key = _parse_user_security_file(user_security_file)
        public_key = _slurp(cluster_public_key)
        return quasardb.Cluster(
            uri,
            user_name=user,
            user_private_key=private_key,
            cluster_public_key=public_key,
        )
    else:
        return quasardb.Cluster(uri)


def _check_node_online(conn):
    logger.info("Checking node online")
    ret = {}

    for endpoint in conn.endpoints():
        ret[endpoint] = 0  # pessimistic
        node = conn.node(endpoint)
        entry = node.integer("$qdb.statistics.startup_epoch")  # entry always exists

        try:
            entry.get()
            ret[endpoint] = 1
        except quasardb.Error as e:
            logger.error(f"[{endpoint}] Failed to read sample entry: {e}")

    return ret


def _check_node_writable(conn):
    logger.info("Checking node writable")
    key = f"_qdb_write_check_{uuid.uuid4().hex}"  # almost zero chance of collision
    value = random.randint(-9223372036854775808, 9223372036854775807)
    ret = {}

    for endpoint in conn.endpoints():
        ret[endpoint] = 0  # pessimistic
        node = conn.node(endpoint)
        entry = node.integer(key)

        try:
            entry.put(value)
            if entry.get() == value:
                ret[endpoint] = 1
        except quasardb.Error as e:
            logger.error(f"[{endpoint}] Failed to put/get test entry '{key}': {e}")
        finally:
            try:
                entry.remove()
            except quasardb.AliasNotFoundError:
                pass
            except quasardb.Error as e:
                logger.error(f"[{endpoint}] Failed to clean up test entry '{key}': {e}")

    return ret


def get_critical_stats(*args, **kwargs):
    """
    Return the minimal set of cluster health metrics required for alerting.

    These metrics (i.e., `check.online` and `node.writable`) are the ones that
    feed CloudWatch alarms and signal conditions that require immediate action.
    By contrast, high-volume or informational metrics (cache usage, RocksDB
    internals, etc.) are non-critical because they are (usually) not part of the
    alerting path.

    Future extensions may allow users to define their own critical metrics.
    """
    logger.info("Getting critical stats")
    with get_qdb_conn(*args, **kwargs) as conn:
        ret = {endpoint: {"cumulative": {}} for endpoint in conn.endpoints()}
        online_stats = _check_node_online(conn)
        writable_stats = _check_node_writable(conn)

        for endpoint in conn.endpoints():
            ret[endpoint]["cumulative"]["check.online"] = {
                "value": online_stats.get(endpoint, 0),
                "type": qdbst.Type.GAUGE,
                "unit": qdbst.Unit.NONE,
            }
            ret[endpoint]["cumulative"]["node.writable"] = {
                "value": writable_stats.get(endpoint, 0),
                "type": qdbst.Type.GAUGE,
                "unit": qdbst.Unit.NONE,
            }

        return ret


def get_all_stats(*args, **kwargs):
    logger.info("Getting all the stats")
    with get_qdb_conn(*args, **kwargs) as conn:
        ret = qdbst.by_node(conn)
        return ret


def _do_filter_metrics(metrics, fn):
    return {key: metrics[key] for key in metrics if fn(key)}


def _do_filter(stats, fn):
    """
    Performs actual filtering of stats, keeping only those where fn(name) equals True
    """

    for node_id in stats:
        for group_id in stats[node_id]:
            if group_id == "cumulative":
                stats[node_id][group_id] = _do_filter_metrics(
                    stats[node_id][group_id], fn
                )
            elif group_id == "by_uid":
                for uid in stats[node_id][group_id]:
                    stats[node_id][group_id][uid] = _do_filter_metrics(
                        stats[node_id][group_id][uid], fn
                    )
            else:
                raise RuntimeError(
                    "Internal error: unrecognized stats group id: {}".format(group_id)
                )
    return stats


def filter_stats(stats, include=None, exclude=None):
    logger.info("Filtering stats based on include/exclude filters")
    stats_ = copy.deepcopy(stats)

    if include is not None:
        # Returns `true` if any of the `include` patterns is found in the metric name.
        def _filter_include(metric_name):
            return any(
                pattern for pattern in include if re.search(pattern, metric_name)
            )

        stats_ = _do_filter(stats_, _filter_include)

    if exclude is not None:
        # Returns `false` if any of the `exclude` patterns is found in the metric name.
        def _filter_exclude(metric_name):
            return not any(
                pattern for pattern in exclude if re.search(pattern, metric_name)
            )

        stats_ = _do_filter(stats_, _filter_exclude)

    return stats_
