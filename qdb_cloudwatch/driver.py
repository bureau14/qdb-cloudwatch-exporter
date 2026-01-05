import argparse
import logging
import sys
from argparse import Namespace

from .check import filter_stats, get_all_stats, get_critical_stats
from .cloudwatch import push_stats

logger = logging.getLogger(__name__)


def _parse_list(x):
    """
    Parses a comma-separated string into a list.
    """

    if x is None or not x.strip():
        return None

    return [token.strip() for token in x.split(",") if token.strip()]


def get_args() -> Namespace:
    """
    Parse and return command-line arguments for exporting QuasarDB metrics to CloudWatch.

    This function defines and parses CLI arguments required to connect to a
    QuasarDB cluster, select a node, optionally filter metrics, and specify
    the target CloudWatch namespace. Include and exclude filters are parsed
    into lists of regular-expression patterns and logged if provided.

    Returns
    -------
    argparse.Namespace
        Parsed command-line arguments with the following attributes:

        - cluster_uri : str
          QuasarDB cluster URI to connect to.
        - cluster_public_key : str or None
          Path to the cluster public key file.
        - user_security_file : str or None
          Path to the user security file containing credentials.
        - node_id : str or None
          Node ID from which to collect metrics.
        - namespace : str
          CloudWatch namespace for published metrics.
        - filter_include : list[str] or None
          List of regex patterns used to include metrics.
        - filter_exclude : list[str] or None
          List of regex patterns used to exclude metrics.

    Notes
    -----
    - Include and exclude filters are expected as comma-separated strings and
      are converted to lists via ``_parse_list``.
    - If both include and exclude filters are provided, include filtering
      is applied first by downstream logic.
    - Default cluster URI is ``qdb://127.0.0.1:2836``.
    """

    parser = argparse.ArgumentParser(
        description=("Fetch QuasarDB metrics for local node and export to CloudWatch.")
    )
    parser.add_argument(
        "--cluster",
        dest="cluster_uri",
        help="QuasarDB cluster uri to connect to. Defaults to qdb://127.0.0.1:2836",
        default="qdb://127.0.0.1:2836",
    )

    parser.add_argument(
        "--cluster-public-key",
        dest="cluster_public_key",
        help="Cluster public key file",
    )

    parser.add_argument(
        "--user-security-file",
        dest="user_security_file",
        help="User security file, containing both username and private access token.",
    )

    parser.add_argument(
        "--node-id",
        dest="node_id",
        help="Node id to collect metrics from, e.g. 0-0-0-1",
    )

    parser.add_argument(
        "--namespace",
        dest="namespace",
        help="Namespace for metrics",
        default="QuasarDB",
    )

    parser.add_argument(
        "--filter-include",
        dest="filter_include",
        help="Optional comma-separated list of regex patterns to filter metrics. Only metrics that match at least one of the patterns will be reported.",
    )

    parser.add_argument(
        "--filter-exclude",
        dest="filter_exclude",
        help="Optional comma-separated list of regex patterns to filter metrics. Only metrics that contain none of the patterns will be reported.",
    )

    ret = parser.parse_args()

    ret.filter_include = _parse_list(ret.filter_include)
    ret.filter_exclude = _parse_list(ret.filter_exclude)

    if ret.filter_include is not None:
        logger.info(f"Using include filters: {ret.filter_include}")

    if ret.filter_exclude is not None:
        logger.info(f"Using exclude filters: {ret.filter_exclude}")

    return ret


def main():
    """
    Entry point for exporting QuasarDB metrics to Amazon CloudWatch.

    This function initializes logging, parses command-line arguments, and
    orchestrates the collection and publication of QuasarDB metrics. Critical
    metrics are fetched and pushed first to ensure timely reporting when the
    cluster is under load, followed by the full metric set with optional
    include/exclude filtering applied.

    Workflow
    --------
    1. Configure logging.
    2. Parse command-line arguments.
    3. Collect and push critical metrics to CloudWatch.
    4. Collect all available metrics.
    5. Apply optional include/exclude filters.
    6. Push filtered metrics to CloudWatch.

    Returns
    -------
    None
    """

    logging.basicConfig(stream=sys.stderr, level=logging.INFO)

    args = get_args()

    # Send critical stats first, as getting all stats is expensive when cluster is busy.
    critical_stats = get_critical_stats(
        args.cluster_uri,
        cluster_public_key=args.cluster_public_key,
        user_security_file=args.user_security_file,
    )
    push_stats(critical_stats, args.namespace)

    stats = get_all_stats(
        args.cluster_uri,
        cluster_public_key=args.cluster_public_key,
        user_security_file=args.user_security_file,
    )
    stats = filter_stats(
        stats, include=args.filter_include, exclude=args.filter_exclude
    )

    push_stats(stats, args.namespace)
