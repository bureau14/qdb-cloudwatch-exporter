import argparse
import quasardb

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
        '--prefix',
        dest='prefix',
        help='Prefix to add to all metrics')
git
    return parser.parse_args()

def get_qdb_conn(uri, cluster_public_key=None, user_security_file=None):
    if cluster_public_key and user_security_file:
        user, private_key = _parse_user_security_file(user_security_file)
        public_key = _slurp(cluster_public_key)
        return quasardb.Cluster(uri,
                                user_name=user,
                                user_private_key=private_key,
                                cluster_public_key=public_key)
    else:
        return quasardb.Cluster(uri)


def main():
    args = get_args()


    with get_qdb_conn(args.cluster_uri,
                      cluster_public_key=args.cluster_public_key,
                      user_security_file=args.user_security_file) as conn:
        print("conn: ", conn)
