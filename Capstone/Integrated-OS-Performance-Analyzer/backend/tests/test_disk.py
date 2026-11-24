from collections import namedtuple
from unittest.mock import patch

import psutil

from app.collectors.disk import DiskCollector
from app.schemas.metrics import (
    DiskIOCountersMetrics,
    DiskMetrics,
    DiskPartitionInfo,
    DiskPartitionMetrics,
    DiskUsageMetrics,
)

MockPartition = namedtuple("sdiskpart", ["device", "mountpoint", "fstype", "opts"])
MockDiskUsage = namedtuple("sdiskusage", ["total", "used", "free", "percent"])
MockDiskIO = namedtuple(
    "sdiskio",
    [
        "read_count",
        "write_count",
        "read_bytes",
        "write_bytes",
        "read_time",
        "write_time",
    ],
)


def test_collector_initialization():
    collector = DiskCollector()
    assert collector._sample_count == 0
    assert collector.last_sampled_at is None
    assert collector.initialized_at.tzinfo is not None


def test_get_disk_partitions_discovery():
    mock_parts = [
        MockPartition(
            device="/dev/sda1", mountpoint="/", fstype="ext4", opts="rw,relatime"
        ),
        MockPartition(device="/dev/sdb1", mountpoint="/data", fstype="xfs", opts="rw"),
    ]

    with patch("psutil.disk_partitions", return_value=mock_parts):
        collector = DiskCollector()
        partitions = collector.get_disk_partitions()

    assert len(partitions) == 2
    assert isinstance(partitions[0], DiskPartitionMetrics)
    assert partitions[0].device == "/dev/sda1"
    assert partitions[0].mountpoint == "/"
    assert partitions[0].filesystem == "ext4"
    assert partitions[0].options == "rw,relatime"
    assert partitions[1].device == "/dev/sdb1"
    assert partitions[1].mountpoint == "/data"
    assert partitions[1].filesystem == "xfs"


def test_get_disk_partitions_empty():
    with patch("psutil.disk_partitions", return_value=[]):
        collector = DiskCollector()
        partitions = collector.get_disk_partitions()

    assert partitions == []


def test_get_disk_partitions_duplicate_mountpoints():
    mock_parts = [
        MockPartition(device="/dev/sda1", mountpoint="/", fstype="ext4", opts="rw"),
        MockPartition(device="/dev/sda1", mountpoint="/", fstype="ext4", opts="rw"),
    ]

    with patch("psutil.disk_partitions", return_value=mock_parts):
        collector = DiskCollector()
        partitions = collector.get_disk_partitions()

    assert len(partitions) == 1
    assert partitions[0].mountpoint == "/"


def test_get_disk_partitions_pseudo_filesystems_filtered():
    mock_parts = [
        MockPartition(device="tmpfs", mountpoint="/tmp", fstype="tmpfs", opts="rw"),
        MockPartition(device="proc", mountpoint="/proc", fstype="proc", opts="rw"),
        MockPartition(device="sysfs", mountpoint="/sys", fstype="sysfs", opts="rw"),
        MockPartition(device="/dev/sda1", mountpoint="/", fstype="ext4", opts="rw"),
    ]

    with patch("psutil.disk_partitions", return_value=mock_parts):
        collector = DiskCollector()
        partitions = collector.get_disk_partitions()

    # Only real ext4 partition should remain
    assert len(partitions) == 1
    assert partitions[0].mountpoint == "/"
    assert partitions[0].filesystem == "ext4"


def test_get_disk_partitions_psutil_error():
    with patch("psutil.disk_partitions", side_effect=psutil.Error("Simulated error")):
        collector = DiskCollector()
        partitions = collector.get_disk_partitions()

    assert partitions == []


def test_get_disk_partitions_os_error():
    with patch("psutil.disk_partitions", side_effect=OSError("Permission denied")):
        collector = DiskCollector()
        partitions = collector.get_disk_partitions()

    assert partitions == []


def test_get_disk_usage_valid():
    mock_usage = MockDiskUsage(
        total=500000000000,
        used=150000000000,
        free=350000000000,
        percent=30.0,
    )

    with patch("psutil.disk_usage", return_value=mock_usage):
        collector = DiskCollector()
        usage = collector.get_disk_usage("/")

    assert isinstance(usage, DiskUsageMetrics)
    assert usage.total == 500000000000
    assert usage.used == 150000000000
    assert usage.free == 350000000000
    assert usage.percent == 30.0


def test_get_disk_usage_inaccessible_mountpoint():
    # E.g. PermissionError on restricted directory
    with patch("psutil.disk_usage", side_effect=PermissionError("Access denied")):
        collector = DiskCollector()
        usage = collector.get_disk_usage("/root/secret")

    assert usage is None


def test_get_disk_usage_os_error():
    # E.g. disconnected network mount or unready drive
    with patch("psutil.disk_usage", side_effect=OSError("Drive not ready")):
        collector = DiskCollector()
        usage = collector.get_disk_usage("D:\\")

    assert usage is None


def test_get_disk_usage_psutil_error():
    with patch("psutil.disk_usage", side_effect=psutil.Error("psutil failure")):
        collector = DiskCollector()
        usage = collector.get_disk_usage("/")

    assert usage is None


def test_get_disk_usage_empty_mountpoint():
    collector = DiskCollector()
    usage = collector.get_disk_usage("")
    assert usage is None


def test_get_disk_io_counters_valid():
    mock_io = MockDiskIO(
        read_count=12000,
        write_count=6000,
        read_bytes=100000000,
        write_bytes=50000000,
        read_time=3000,
        write_time=1500,
    )

    with patch("psutil.disk_io_counters", return_value=mock_io):
        collector = DiskCollector()
        counters = collector.get_disk_io_counters()

    assert isinstance(counters, DiskIOCountersMetrics)
    assert counters.read_count == 12000
    assert counters.write_count == 6000
    assert counters.read_bytes == 100000000
    assert counters.write_bytes == 50000000
    assert counters.read_time == 3000
    assert counters.write_time == 1500


def test_get_disk_io_counters_none_unavailable():
    # On VMs or containers with no disk I/O stats
    with patch("psutil.disk_io_counters", return_value=None):
        collector = DiskCollector()
        counters = collector.get_disk_io_counters()

    assert counters is None


def test_get_disk_io_counters_exception():
    with patch("psutil.disk_io_counters", side_effect=psutil.Error("I/O error")):
        collector = DiskCollector()
        counters = collector.get_disk_io_counters()

    assert counters is None


def test_get_disk_metrics_combined_success():
    mock_parts = [
        MockPartition(device="/dev/sda1", mountpoint="/", fstype="ext4", opts="rw"),
        MockPartition(device="/dev/sdb1", mountpoint="/home", fstype="ext4", opts="rw"),
    ]
    mock_usage_root = MockDiskUsage(
        total=100000000000, used=40000000000, free=60000000000, percent=40.0
    )
    mock_usage_home = MockDiskUsage(
        total=200000000000, used=50000000000, free=150000000000, percent=25.0
    )
    mock_io = MockDiskIO(
        read_count=500,
        write_count=200,
        read_bytes=10000,
        write_bytes=5000,
        read_time=100,
        write_time=50,
    )

    def side_effect_usage(mountpoint):
        if mountpoint == "/":
            return mock_usage_root
        elif mountpoint == "/home":
            return mock_usage_home
        return None

    with (
        patch("psutil.disk_partitions", return_value=mock_parts),
        patch("psutil.disk_usage", side_effect=side_effect_usage),
        patch("psutil.disk_io_counters", return_value=mock_io),
    ):
        collector = DiskCollector()
        metrics = collector.get_disk_metrics()

    assert isinstance(metrics, DiskMetrics)
    assert len(metrics.partitions) == 2
    assert isinstance(metrics.partitions[0], DiskPartitionInfo)
    assert metrics.partitions[0].partition.mountpoint == "/"
    assert metrics.partitions[0].usage is not None
    assert metrics.partitions[0].usage.total == 100000000000
    assert metrics.partitions[0].usage.percent == 40.0

    assert metrics.partitions[1].partition.mountpoint == "/home"
    assert metrics.partitions[1].usage is not None
    assert metrics.partitions[1].usage.total == 200000000000
    assert metrics.partitions[1].usage.percent == 25.0

    assert metrics.io_counters is not None
    assert metrics.io_counters.read_count == 500
    assert metrics.timestamp.tzinfo is not None


def test_get_disk_metrics_partial_inaccessible_partitions():
    mock_parts = [
        MockPartition(device="/dev/sda1", mountpoint="/", fstype="ext4", opts="rw"),
        MockPartition(
            device="/dev/sdc1", mountpoint="/restricted", fstype="ext4", opts="rw"
        ),
    ]
    mock_usage_root = MockDiskUsage(
        total=100000000000, used=40000000000, free=60000000000, percent=40.0
    )

    def side_effect_usage(mountpoint):
        if mountpoint == "/":
            return mock_usage_root
        if mountpoint == "/restricted":
            raise PermissionError("Access denied")
        return None

    with (
        patch("psutil.disk_partitions", return_value=mock_parts),
        patch("psutil.disk_usage", side_effect=side_effect_usage),
        patch("psutil.disk_io_counters", return_value=None),
    ):
        collector = DiskCollector()
        metrics = collector.get_disk_metrics()

    assert len(metrics.partitions) == 2
    # First partition is accessible
    assert metrics.partitions[0].partition.mountpoint == "/"
    assert metrics.partitions[0].usage is not None
    assert metrics.partitions[0].usage.percent == 40.0
    # Second partition is inaccessible: metadata preserved, usage is None
    assert metrics.partitions[1].partition.mountpoint == "/restricted"
    assert metrics.partitions[1].usage is None
    # I/O counters None
    assert metrics.io_counters is None


def test_get_disk_metrics_all_inaccessible_partitions():
    mock_parts = [
        MockPartition(
            device="/dev/sda1", mountpoint="/ inaccessible1", fstype="ext4", opts="rw"
        ),
        MockPartition(
            device="/dev/sda2", mountpoint="/ inaccessible2", fstype="ext4", opts="rw"
        ),
    ]

    with (
        patch("psutil.disk_partitions", return_value=mock_parts),
        patch("psutil.disk_usage", side_effect=PermissionError("Permission denied")),
        patch("psutil.disk_io_counters", return_value=None),
    ):
        collector = DiskCollector()
        metrics = collector.get_disk_metrics()

    assert len(metrics.partitions) == 2
    assert metrics.partitions[0].usage is None
    assert metrics.partitions[1].usage is None


def test_get_disk_metrics_empty_partitions():
    with (
        patch("psutil.disk_partitions", return_value=[]),
        patch("psutil.disk_io_counters", return_value=None),
    ):
        collector = DiskCollector()
        metrics = collector.get_disk_metrics()

    assert metrics.partitions == []
    assert metrics.io_counters is None


def test_get_disk_metrics_timestamp_consistency():
    collector = DiskCollector()
    metrics = collector.get_disk_metrics()
    assert metrics.timestamp == collector.last_sampled_at


def test_collector_repeated_calls_increment_sample_count():
    with (
        patch("psutil.disk_partitions", return_value=[]),
        patch("psutil.disk_io_counters", return_value=None),
    ):
        collector = DiskCollector()
        assert collector._sample_count == 0

        collector.get_disk_partitions()
        assert collector._sample_count == 1

        collector.get_disk_usage("/fake")
        assert collector._sample_count == 2

        collector.get_disk_io_counters()
        assert collector._sample_count == 3

        collector.get_disk_metrics()
        assert collector._sample_count == 4


def test_collector_instances_do_not_share_state():
    c1 = DiskCollector()
    c2 = DiskCollector()

    with (
        patch("psutil.disk_partitions", return_value=[]),
        patch("psutil.disk_io_counters", return_value=None),
    ):
        c1.get_disk_metrics()

    assert c1._sample_count == 1
    assert c1.last_sampled_at is not None
    assert c2._sample_count == 0
    assert c2.last_sampled_at is None


def test_collector_real_system_smoke():
    """Live smoke test on real host verifying collector robustness."""
    collector = DiskCollector()

    partitions = collector.get_disk_partitions()
    assert isinstance(partitions, list)

    for part in partitions:
        assert isinstance(part.device, str)
        assert isinstance(part.mountpoint, str)
        usage = collector.get_disk_usage(part.mountpoint)
        if usage is not None:
            assert isinstance(usage, DiskUsageMetrics)
            assert usage.total >= 0
            assert usage.used >= 0
            assert usage.free >= 0
            assert 0.0 <= usage.percent <= 100.0

    io = collector.get_disk_io_counters()
    if io is not None:
        assert isinstance(io, DiskIOCountersMetrics)
        assert io.read_count >= 0
        assert io.write_count >= 0
        assert io.read_bytes >= 0
        assert io.write_bytes >= 0

    combined = collector.get_disk_metrics()
    assert isinstance(combined, DiskMetrics)
    assert combined.timestamp.tzinfo is not None
    assert collector._sample_count >= 1


def test_get_disk_partitions_deduplicate_same_device_different_mountpoints():
    """Verify duplicate mountpoints sharing the same underlying block device are deduplicated."""
    mock_parts = [
        MockPartition(
            device="/dev/sdd",
            mountpoint="/",
            fstype="ext4",
            opts="rw,relatime,discard,errors=remount-ro",
        ),
        MockPartition(
            device="/dev/sdd",
            mountpoint="/mnt/wslg/distro",
            fstype="ext4",
            opts="ro,relatime,discard",
        ),
    ]

    with patch("psutil.disk_partitions", return_value=mock_parts):
        collector = DiskCollector()
        partitions = collector.get_disk_partitions()

    # Must be deduplicated to 1 unique partition
    assert len(partitions) == 1
    p = partitions[0]
    assert p.device == "/dev/sdd"
    assert p.mountpoint == "/"  # Primary canonical mountpoint
    assert "/" in p.mountpoints
    assert "/mnt/wslg/distro" in p.mountpoints
    assert len(p.mountpoints) == 2


def test_disk_metrics_deduplication_and_aggregate_calculations():
    """Verify aggregate capacity, used, and percent do not inflate due to duplicate mounts."""
    mock_parts = [
        MockPartition(device="/dev/sdd", mountpoint="/", fstype="ext4", opts="rw"),
        MockPartition(
            device="/dev/sdd", mountpoint="/mnt/wslg/distro", fstype="ext4", opts="ro"
        ),
    ]
    mock_usage = MockDiskUsage(
        total=1081101176832, used=6951653376, free=1019183439872, percent=0.7
    )

    with (
        patch("psutil.disk_partitions", return_value=mock_parts),
        patch("psutil.disk_usage", return_value=mock_usage),
        patch("psutil.disk_io_counters", return_value=None),
    ):
        collector = DiskCollector()
        metrics = collector.get_disk_metrics()

    # Partitions list must contain only unique filesystems
    assert len(metrics.partitions) == 1
    assert metrics.unique_partition_count == 1
    # Total capacity must be counted ONCE (not 2 x 1081101176832)
    assert metrics.total_capacity_bytes == 1081101176832
    assert metrics.total_used_bytes == 6951653376
    assert metrics.total_percent == 0.6 or metrics.total_percent == 0.7


def test_disk_metrics_real_system_wsl2_deduplication():
    """Verify live system disk metrics correctly deduplicate /dev/sdd on WSL2."""
    collector = DiskCollector()
    metrics = collector.get_disk_metrics()

    devices = [p.partition.device for p in metrics.partitions if p.partition.device]
    # All devices must be unique (no duplicate /dev/sdd)
    assert len(devices) == len(set(devices))
    assert metrics.unique_partition_count == len(metrics.partitions)

    # In WSL2 environment where /dev/sdd is the primary disk
    sdd_parts = [p for p in metrics.partitions if p.partition.device == "/dev/sdd"]
    if sdd_parts:
        assert len(sdd_parts) == 1
        assert sdd_parts[0].partition.mountpoint == "/"
        assert "/" in sdd_parts[0].partition.mountpoints
