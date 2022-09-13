import json
import random

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


def _check_node_writable(conn):
    value = random.randint(-9223372036854775808, 9223372036854775807)
    ret = {}
    for endpoint in conn.endpoints():
        ret[endpoint] = 1
        node = conn.node(endpoint)
        entry = node.integer('check_direct')

        # remove old entry
        try:
            entry.remove()
        except:
            pass

        # put, get, compare, remove
        try:
            entry.put(value)
            entry_value = entry.get()
            if entry_value != value:
                ret[endpoint] = 0
                continue
            entry.remove()
        except Exception as e:
            ret[endpoint] = 0
            continue

        # verify whether the entry was removed
        try:
            entry.get()
        except quasardb.quasardb.AliasNotFoundError:
            pass
        except Exception as e:
            ret[endpoint] = 0
            continue

    return ret


def get_stats(*args, **kwargs):
    with get_qdb_conn(*args, **kwargs) as conn:
        stats = qdbst.by_node(conn)
        for endpoint, result in _check_node_writable(conn).items():
            stats[endpoint]['cumulative']['node.writable'] = result
        return stats
