import json

import quasardb
import quasardb.stats as qdbst

def _slurp(x):
    with open(x, 'r') as fp:
        return fp.read()

def _parse_user_security_file(x):
    with open(x, 'r') as fp:
        parsed = json.load(fp)
        return (parsed['username'], parsed['secret_key'])

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


def get_stats(*args, **kwargs):
    with get_qdb_conn(*args, **kwargs) as conn:
        return qdbst.by_node(conn)
