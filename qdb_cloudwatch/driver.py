import argparse

from .check import get_stats, filter_stats
from .cloudwatch import push_stats

def _parse_list(x):
    """
    Parses a comma-separated string into a list.
    """

    if x is None:
        return x

    return [token.strip() for token in x.split(',')]

def get_args():
    parser = argparse.ArgumentParser(
        description=(
            'Fetch QuasarDB metrics for local node and export to CloudWatch.'))
    parser.add_argument(
        '--cluster',
        dest='cluster_uri',
        help='QuasarDB cluster uri to connect to. Defaults to qdb://127.0.0.1:2836',
        default="qdb://127.0.0.1:2836")

    parser.add_argument(
        '--cluster-public-key',
        dest='cluster_public_key',
        help='Cluster public key file')

    parser.add_argument(
        '--user-security-file',
        dest='user_security_file',
        help='User security file, containing both username and private access token.')

    parser.add_argument(
        '--node-id',
        dest='node_id',
        help='Node id to collect metrics from, e.g. 0-0-0-1')

    parser.add_argument(
        '--namespace',
        dest='namespace',
        help='Namespace for metrics',
        default='QuasarDB')

    parser.add_argument(
        '--filter-include',
        dest='filter_include',
        help='Optional comma-separated list of string patterns to use to filter metrics for. Only metrics that match at least one of the patterns will be reported.')

    parser.add_argument(
        '--filter-exclude',
        dest='filter_exclude',
        help='Optional comma-separated list of string patterns to use to filter metrics for. Only metrics that contain none of the patterns will be reported.')

    ret = parser.parse_args()

    ret.filter_include = _parse_list(ret.filter_include)
    ret.filter_exclude = _parse_list(ret.filter_exclude)

    if ret.filter_include is not None:
        print("Using include filters: ", ret.filter_include)

    if ret.filter_exclude is not None:
        print("Using exclude filters: ", ret.filter_exclude)

    return ret

def main():
    args = get_args()
    stats = get_stats(args.cluster_uri,
                      cluster_public_key=args.cluster_public_key,
                      user_security_file=args.user_security_file)

    stats = filter_stats(stats, include=args.filter_include, exclude=args.filter_exclude)

    push_stats(stats, args.namespace)
