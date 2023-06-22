import pytest
import quasardb
from qdb_cloudwatch.check import filter_stats

def test_filter_single_include(stats):
    stats_ = filter_stats(stats, include=["perf."])

    assert stats_ != stats

    for node_id in stats_:
        for metric_name in stats_[node_id]['cumulative']:
            assert "perf." in metric_name

        for uid in stats_[node_id]['by_uid']:
            for metric_name in stats_[node_id]['by_uid'][uid]:
                assert "perf." in metric_name


def test_filter_multiple_include(stats):
    stats_ = filter_stats(stats, include=["perf.", "network."])

    assert stats_ != stats

    # Also ensure that the result is actually different now that we also allow "network" to be returned
    assert stats_ != filter_stats(stats, include=["perf."])

    for node_id in stats_:
        for metric_name in stats_[node_id]['cumulative']:
            assert "perf." in metric_name or "network." in metric_name

        for uid in stats_[node_id]['by_uid']:
            for metric_name in stats_[node_id]['by_uid'][uid]:
                assert "perf." in metric_name or "network." in metric_name


def test_filter_single_exclude(stats):
    stats_ = filter_stats(stats, exclude=["perf."])

    assert stats_ != stats

    for node_id in stats_:
        for metric_name in stats_[node_id]['cumulative']:
            assert "perf." not in metric_name

        for uid in stats_[node_id]['by_uid']:
            for metric_name in stats_[node_id]['by_uid'][uid]:
                assert "perf." not in metric_name


def test_filter_multiple_exclude(stats):
    stats_ = filter_stats(stats, exclude=["perf.", "network."])

    assert stats_ != stats

    # Also ensure that the result is actually different now that we also allow "network" to be returned
    assert stats_ != filter_stats(stats, exclude=["perf."])
    assert stats_ != filter_stats(stats, include=["perf."])
    assert stats_ != filter_stats(stats, include=["perf.", "network."])


    for node_id in stats_:
        for metric_name in stats_[node_id]['cumulative']:
            assert "perf." not in metric_name
            assert "network." not in metric_name

        for uid in stats_[node_id]['by_uid']:
            for metric_name in stats_[node_id]['by_uid'][uid]:
                assert "perf." not in metric_name
                assert "network." not in metric_name
