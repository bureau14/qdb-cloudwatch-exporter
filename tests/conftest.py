# pylint: disable=C0103,C0111,C0302,W0212
import datetime
import json
import pprint

import pytest
import quasardb

from qdb_cloudwatch.check import get_stats

pp = pprint.PrettyPrinter()


def connect(uri):
    return quasardb.Cluster(uri)


def config():
    return {
        "uri": {"insecure": "qdb://127.0.0.1:2836", "secure": "qdb://127.0.0.1:2838"}
    }


def _qdbd_settings():
    user_key = {}
    cluster_key = ""

    with open("user_private.key", "r") as user_key_file:
        user_key = json.load(user_key_file)
    with open("cluster_public.key", "r") as cluster_key_file:
        cluster_key = cluster_key_file.read()
    return {
        "uri": "qdb://127.0.0.1:2838",
        "security": {
            "user_name": user_key["username"],
            "user_private_key": user_key["secret_key"],
            "cluster_public_key": cluster_key,
            "user_private_key_file": "user_private.key",
            "cluster_public_key_file": "cluster_public.key",
        },
    }


@pytest.fixture(scope="module")
def qdbd_settings():
    return _qdbd_settings()


def create_qdbd_connection(settings, purge=False):
    conn = connect(settings.get("uri").get("insecure"))

    if purge is True:
        conn.purge_all(datetime.timedelta(minutes=1))

    return conn


@pytest.fixture(scope="module")
def qdbd_connection(qdbd_settings):
    conn = quasardb.Cluster(
        uri=qdbd_settings.get("uri"),
        user_name=qdbd_settings.get("security").get("user_name"),
        user_private_key=qdbd_settings.get("security").get("user_private_key"),
        cluster_public_key=qdbd_settings.get("security").get("cluster_public_key"),
    )
    conn.purge_all(datetime.timedelta(minutes=1))
    yield conn
    conn.close()


@pytest.fixture(params=["secure", "insecure"])
def qdbd_direct_connection(request):
    settings = _qdbd_settings()

    if request.param == "insecure":
        return quasardb.Node(settings.get("uri").get("insecure").replace("qdb://", ""))
    elif request.param == "secure":
        return quasardb.Node(
            settings.get("uri").get("secure").replace("qdb://", ""),
            user_name=settings.get("security").get("user_name"),
            user_private_key=settings.get("security").get("user_private_key"),
            cluster_public_key=settings.get("security").get("cluster_public_key"),
        )


@pytest.fixture(scope="module")
def stats(qdbd_settings):
    return get_stats(
        qdbd_settings.get("uri"),
        cluster_public_key=qdbd_settings.get("security").get("cluster_public_key_file"),
        user_security_file=qdbd_settings.get("security").get("user_private_key_file"),
    )
