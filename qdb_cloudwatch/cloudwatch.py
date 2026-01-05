import logging

import boto3
from quasardb.stats import Unit
from botocore.client import BaseClient

logger = logging.getLogger(__name__)

_stat_unit_to_cloudwatch_unit = {
    Unit.NONE: "None",
    Unit.COUNT: "Count",
    Unit.BYTES: "Bytes",
    Unit.EPOCH: "None",
    Unit.NANOSECONDS: "None",
    Unit.MICROSECONDS: "Microseconds",
    Unit.MILLISECONDS: "Milliseconds",
    Unit.SECONDS: "Seconds",
}


def _get_client() -> BaseClient:
    logger.info("Getting cloudwatch client")
    return boto3.client("cloudwatch")


def _coerce_metric(k, v) -> tuple | None:
    if k.startswith("cpu."):
        # We don't expose CPU metrics through Cloudwatch, as this is already collected
        # by the regular metrics.
        return None

    if v["unit"] == Unit.NANOSECONDS:
        v["unit"] = Unit.MICROSECONDS
        v["value"] /= 1000

    return (_stat_unit_to_cloudwatch_unit.get(v["unit"], "None"), float(v["value"]))


def _to_metric(k, v) -> dict | None:
    try:
        x = _coerce_metric(k, v)
        if x:
            (u, v_) = x
            return {"MetricName": k, "Value": v_, "Unit": u}
    except:
        logger.debug(f"The key '{k}' cannot be sent")
        return None


def _qdb_to_cloudwatch(stats: dict) ->  list:
    # We want to flatten all metrics into a tuple of 3 items:
    # - node_id
    # - user_id
    # - measurement

    ret = list()

    for node_id, xs in stats.items():
        for user_id, xs_ in xs["by_uid"].items():
            dims = [
                {"Name": "UserId", "Value": str(user_id)},
                {"Name": "NodeId", "Value": str(node_id)},
            ]
            for k, v in xs_.items():
                m = _to_metric(k, v)
                if m:
                    m["Dimensions"] = dims
                    ret.append(m)

        dims = [{"Name": "NodeId", "Value": str(node_id)}]
        for k, v in xs["cumulative"].items():
            m = _to_metric(k, v)
            if m:
                m["Dimensions"] = dims
                ret.append(m)

    return ret


def push_stats(stats: dict, namespace: str) -> None:
    """
    Push a collection of statistics to Amazon CloudWatch under a given namespace.

    This function converts QuasarDB-style statistics into CloudWatch-compatible
    metric data and publishes them using the CloudWatch ``PutMetricData`` API.
    Metrics are batched to comply with CloudWatch limits (maximum of 20 metrics
    per request).

    Parameters
    ----------
    stats : dict
        Dictionary of statistics to be published, keyed by metric name.
    namespace : str
        CloudWatch namespace under which the metrics will be recorded.

    Returns
    -------
    None

    Notes
    -----
    - Metrics are transformed via ``_qdb_to_cloudwatch`` before submission.
    - Metrics are sent in batches of 20 to comply with CloudWatch API limits.
    - Progress is logged before and after publishing metrics.
    """

    client = _get_client()
    stats_ = _qdb_to_cloudwatch(stats)

    metrics_per_req = 20
    metrics = [
        stats_[i : i + metrics_per_req] for i in range(0, len(stats_), metrics_per_req)
    ]

    logger.info(f"Pushing {len(stats_)} metrics")
    for metric in metrics:
        _ = client.put_metric_data(Namespace=namespace, MetricData=metric)

    logger.info(f"Pushed {len(stats_)} metrics")
