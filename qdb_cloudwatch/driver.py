import argparse

from .check import get_stats
from .cloudwatch import push_stats

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
        '--sts-role-arn',
        dest='sts_role_arn',
        help='Explicitly assume role')

    parser.add_argument(
        '--sts-external-id',
        dest='sts_external_id',
        help='Optional external id to provide with role')

    return parser.parse_args()

def main():
    args = get_args()
    stats = get_stats(args.cluster_uri,
                      cluster_public_key=args.cluster_public_key,
                      user_security_file=args.user_security_file)

    push_stats(stats, args)
