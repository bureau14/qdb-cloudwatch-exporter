import pytest

from qdb_cloudwatch.check import get_all_stats


def test_get_stats(qdbd_settings):
    stats = get_all_stats(
        qdbd_settings.get("uri"),
        qdbd_settings.get("security").get("cluster_public_key_file"),
        qdbd_settings.get("security").get("user_security_file"),
    )

    for node_id in stats.keys():
        # node_id is ip:port, uri is qdb://ip:port
        assert node_id in qdbd_settings.get("uri")

        assert "by_uid" in stats[node_id]
        assert "cumulative" in stats[node_id]
