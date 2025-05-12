import pytest

from qdb_cloudwatch.check import filter_stats


def test_filter_single_include(stats):
    stats_ = filter_stats(stats, include=["memory."])

    assert stats_ != stats

    for node_id in stats_:
        for metric_name in stats_[node_id]["cumulative"]:
            assert "memory." in metric_name

        for uid in stats_[node_id]["by_uid"]:
            for metric_name in stats_[node_id]["by_uid"][uid]:
                assert "memory." in metric_name


def test_filter_multiple_include(stats):
    stats_ = filter_stats(stats, include=["memory.", "network."])

    assert stats_ != stats

    # Also ensure that the result is actually different now that we also allow "network" to be returned
    assert stats_ != filter_stats(stats, include=["memory."])

    for node_id in stats_:
        for metric_name in stats_[node_id]["cumulative"]:
            assert "memory." in metric_name or "network." in metric_name

        for uid in stats_[node_id]["by_uid"]:
            for metric_name in stats_[node_id]["by_uid"][uid]:
                assert "memory." in metric_name or "network." in metric_name


def test_filter_single_exclude(stats):
    stats_ = filter_stats(stats, exclude=["memory."])

    assert stats_ != stats

    for node_id in stats_:
        for metric_name in stats_[node_id]["cumulative"]:
            assert "memory." not in metric_name

        for uid in stats_[node_id]["by_uid"]:
            for metric_name in stats_[node_id]["by_uid"][uid]:
                assert "memory." not in metric_name


def test_filter_multiple_exclude(stats):
    stats_ = filter_stats(stats, exclude=["memory.", "network."])

    assert stats_ != stats

    # Also ensure that the result is actually different now that we also allow "network" to be returned
    assert stats_ != filter_stats(stats, exclude=["memory."])
    assert stats_ != filter_stats(stats, include=["memory."])
    assert stats_ != filter_stats(stats, include=["memory.", "network."])

    for node_id in stats_:
        for metric_name in stats_[node_id]["cumulative"]:
            assert "memory." not in metric_name
            assert "network." not in metric_name

        for uid in stats_[node_id]["by_uid"]:
            for metric_name in stats_[node_id]["by_uid"][uid]:
                assert "memory." not in metric_name
                assert "network." not in metric_name
