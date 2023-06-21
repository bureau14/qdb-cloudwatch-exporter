import pytest
from qdb_cloudwatch.check import get_stats

def test_get_stats(qdbd_settings):
    stats = get_stats(qdbd_settings.get("uri"),
                      cluster_public_key=qdbd_settings.get("security").get("cluster_public_key_file"),
                      user_security_file=qdbd_settings.get("security").get("user_private_key_file"))

    assert 0 == 0
