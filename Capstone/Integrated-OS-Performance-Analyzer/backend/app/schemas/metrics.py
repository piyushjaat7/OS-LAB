from datetime import UTC, datetime

from pydantic import BaseModel, Field, field_validator


class CPUFrequency(BaseModel):
    """CPU core frequency statistics in MHz."""

    current: float | None = Field(
        default=None,
        ge=0.0,
        description="Current operating CPU frequency in MHz",
    )
    min: float | None = Field(
        default=None,
        ge=0.0,
        description="Minimum supported CPU frequency in MHz",
    )
    max: float | None = Field(
        default=None,
        ge=0.0,
        description="Maximum supported CPU frequency in MHz",
    )


class CPUMetrics(BaseModel):
    """System-wide and per-core CPU performance metrics."""

    usage_percent: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Overall CPU utilization percentage (0.0 to 100.0), or None if baseline interval not elapsed",
    )
    per_core_usage: list[float] | None = Field(
        default=None,
        description="CPU utilization percentage per logical core, or None if baseline interval not elapsed",
    )
    physical_cores: int = Field(
        ge=0,
        description="Number of physical CPU cores (0 if undetermined)",
    )
    logical_cores: int = Field(
        ge=0,
        description="Number of logical CPU cores (0 if undetermined)",
    )
    frequency: CPUFrequency | None = Field(
        default=None,
        description="CPU clock frequency statistics in MHz, if supported",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Timezone-aware UTC timestamp of metric sample",
    )

    @field_validator("per_core_usage")
    @classmethod
    def validate_per_core_usage(cls, v: list[float] | None) -> list[float] | None:
        if v is None:
            return v
        for idx, usage in enumerate(v):
            if not (0.0 <= usage <= 100.0):
                raise ValueError(
                    f"Core {idx} utilization must be between 0.0 and 100.0, got {usage}"
                )
        return v

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None or v.utcoffset() is None:
            raise ValueError("Timestamp must be timezone-aware (UTC)")
        return v


class VirtualMemoryMetrics(BaseModel):
    """System virtual memory (RAM) statistics in bytes."""

    total: int = Field(
        ge=0,
        description="Total physical RAM in bytes",
    )
    available: int = Field(
        ge=0,
        description="Memory available for allocation without swapping, in bytes",
    )
    used: int = Field(
        ge=0,
        description="Memory currently allocated and used by processes, in bytes",
    )
    free: int = Field(
        ge=0,
        description="Completely unallocated physical memory in bytes",
    )
    percent: float = Field(
        ge=0.0,
        le=100.0,
        description="Percentage of RAM utilized (0.0 to 100.0)",
    )


class SwapMemoryMetrics(BaseModel):
    """System swap memory statistics in bytes."""

    total: int = Field(
        ge=0,
        description="Total swap space in bytes (0 if disabled or absent)",
    )
    used: int = Field(
        ge=0,
        description="Used swap space in bytes",
    )
    free: int = Field(
        ge=0,
        description="Free swap space in bytes",
    )
    percent: float = Field(
        ge=0.0,
        le=100.0,
        description="Percentage of swap space utilized (0.0 to 100.0)",
    )
    sin: int = Field(
        ge=0,
        description="Cumulative bytes swapped in from disk (0 on Windows)",
    )
    sout: int = Field(
        ge=0,
        description="Cumulative bytes swapped out to disk (0 on Windows)",
    )


class MemoryMetrics(BaseModel):
    """Combined system memory performance metrics."""

    virtual: VirtualMemoryMetrics = Field(description="Virtual RAM telemetry metrics")
    swap: SwapMemoryMetrics = Field(description="Swap memory telemetry metrics")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Timezone-aware UTC timestamp of memory sample",
    )

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None or v.utcoffset() is None:
            raise ValueError("Timestamp must be timezone-aware (UTC)")
        return v


class DiskPartitionMetrics(BaseModel):
    """Metadata describing an individual mounted disk partition."""

    device: str = Field(
        description="Device identifier (e.g. /dev/sda1, C:\\)",
    )
    mountpoint: str = Field(
        description="Mountpoint directory or drive letter",
    )
    filesystem: str = Field(
        description="Filesystem type (e.g. ext4, ntfs, xfs, FAT32)",
    )
    options: str | None = Field(
        default=None,
        description="Mount options string (e.g. rw, relatime, discard)",
    )
    mountpoints: list[str] = Field(
        default_factory=list,
        description="All mountpoint directories where this unique filesystem/device is mounted",
    )


class DiskUsageMetrics(BaseModel):
    """Storage capacity and utilization for a specific mounted partition in bytes."""

    total: int = Field(
        ge=0,
        description="Total storage capacity in bytes",
    )
    used: int = Field(
        ge=0,
        description="Used storage capacity in bytes",
    )
    free: int = Field(
        ge=0,
        description="Free storage capacity available to non-privileged users, in bytes",
    )
    percent: float = Field(
        ge=0.0,
        le=100.0,
        description="Percentage of storage space utilized (0.0 to 100.0)",
    )


class DiskIOCountersMetrics(BaseModel):
    """Cumulative system-wide disk I/O performance counters."""

    read_count: int = Field(
        ge=0,
        description="Cumulative number of disk read operations",
    )
    write_count: int = Field(
        ge=0,
        description="Cumulative number of disk write operations",
    )
    read_bytes: int = Field(
        ge=0,
        description="Cumulative number of bytes read from disk",
    )
    write_bytes: int = Field(
        ge=0,
        description="Cumulative number of bytes written to disk",
    )
    read_time: int = Field(
        ge=0,
        description="Cumulative time spent reading from disk in milliseconds (0 if unsupported)",
    )
    write_time: int = Field(
        ge=0,
        description="Cumulative time spent writing to disk in milliseconds (0 if unsupported)",
    )


class DiskPartitionInfo(BaseModel):
    """Mounted partition metadata paired with its storage usage telemetry."""

    partition: DiskPartitionMetrics = Field(
        description="Partition metadata (device, mountpoint, filesystem, options)",
    )
    usage: DiskUsageMetrics | None = Field(
        default=None,
        description="Storage capacity and utilization metrics, or None if partition is inaccessible",
    )


class DiskMetrics(BaseModel):
    """Combined system storage and disk performance metrics."""

    partitions: list[DiskPartitionInfo] = Field(
        default_factory=list,
        description="List of mounted partitions and their storage utilization",
    )
    io_counters: DiskIOCountersMetrics | None = Field(
        default=None,
        description="Cumulative system-wide disk I/O performance counters, or None if unavailable",
    )
    total_capacity_bytes: int | None = Field(
        default=None,
        description="Aggregate capacity across unique filesystems in bytes",
    )
    total_used_bytes: int | None = Field(
        default=None,
        description="Aggregate used storage across unique filesystems in bytes",
    )
    total_free_bytes: int | None = Field(
        default=None,
        description="Aggregate free storage across unique filesystems in bytes",
    )
    total_percent: float | None = Field(
        default=None,
        description="Overall storage utilization percentage across unique filesystems",
    )
    unique_partition_count: int | None = Field(
        default=None,
        description="Total count of unique physical filesystems/devices",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Timezone-aware UTC timestamp of disk sample",
    )

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None or v.utcoffset() is None:
            raise ValueError("Timestamp must be timezone-aware (UTC)")
        return v


class NetworkIOCountersMetrics(BaseModel):
    """Cumulative network traffic and error counters."""

    bytes_sent: int = Field(
        ge=0,
        description="Cumulative number of bytes sent across the network",
    )
    bytes_recv: int = Field(
        ge=0,
        description="Cumulative number of bytes received across the network",
    )
    packets_sent: int = Field(
        ge=0,
        description="Cumulative number of network packets sent",
    )
    packets_recv: int = Field(
        ge=0,
        description="Cumulative number of network packets received",
    )
    errin: int = Field(
        ge=0,
        description="Cumulative number of transmission errors while receiving",
    )
    errout: int = Field(
        ge=0,
        description="Cumulative number of transmission errors while sending",
    )
    dropin: int = Field(
        ge=0,
        description="Cumulative number of incoming packets dropped",
    )
    dropout: int = Field(
        ge=0,
        description="Cumulative number of outgoing packets dropped",
    )


class NetworkThroughputMetrics(BaseModel):
    """Instantaneous network transmission throughput calculated from consecutive counter samples."""

    bytes_sent_per_sec: float | None = Field(
        default=None,
        ge=0.0,
        description="Instantaneous upload throughput in bytes per second, or None if unavailable/first reading",
    )
    bytes_recv_per_sec: float | None = Field(
        default=None,
        ge=0.0,
        description="Instantaneous download throughput in bytes per second, or None if unavailable/first reading",
    )


class NetworkInterfaceMetrics(BaseModel):
    """Metadata and telemetry for an individual network interface."""

    name: str = Field(
        description="Network interface identifier (e.g. eth0, wlan0, lo)",
    )
    is_up: bool = Field(
        description="Operational link state (True if interface is up, False otherwise)",
    )
    speed: int | None = Field(
        default=None,
        ge=0,
        description="Interface link speed in Mbps (None if undetermined)",
    )
    mtu: int | None = Field(
        default=None,
        ge=0,
        description="Maximum Transmission Unit (MTU) in bytes (None if undetermined)",
    )
    addresses: list[str] | None = Field(
        default=None,
        description="Non-sensitive address metadata (e.g. MAC address, address families)",
    )
    io_counters: NetworkIOCountersMetrics | None = Field(
        default=None,
        description="Cumulative I/O counters for this interface",
    )
    throughput: NetworkThroughputMetrics | None = Field(
        default=None,
        description="Instantaneous throughput for this interface, or None if unavailable/first sample",
    )


class NetworkMetrics(BaseModel):
    """Combined system-wide network telemetry and interface metrics."""

    interfaces: list[NetworkInterfaceMetrics] = Field(
        default_factory=list,
        description="List of detected network interfaces and their respective metrics",
    )
    io_counters: NetworkIOCountersMetrics | None = Field(
        default=None,
        description="System-wide aggregate cumulative network I/O counters, or None if unavailable",
    )
    throughput: NetworkThroughputMetrics | None = Field(
        default=None,
        description="System-wide aggregate instantaneous network throughput, or None if first sample/unavailable",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Timezone-aware UTC timestamp of network sample",
    )

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None or v.utcoffset() is None:
            raise ValueError("Timestamp must be timezone-aware (UTC)")
        return v


class ProcessMetrics(BaseModel):
    """Telemetry metrics for an individual operating system process."""

    pid: int = Field(
        ge=0,
        description="Process ID (PID)",
    )
    name: str = Field(
        description="Process executable name (without directory path)",
    )
    status: str = Field(
        description="Current process execution state (e.g. running, sleeping, idle, zombie)",
    )
    cpu_percent: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Process CPU utilization percentage (0.0 to 100.0), or None if initial reading",
    )
    memory_rss: int = Field(
        ge=0,
        description="Resident Set Size (non-swapped physical memory) in bytes",
    )
    memory_vms: int = Field(
        ge=0,
        description="Virtual Memory Size in bytes",
    )
    memory_percent: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Memory utilization percentage of total physical RAM (0.0 to 100.0)",
    )
    num_threads: int = Field(
        default=1,
        ge=0,
        description="Number of active execution threads",
    )
    create_time: float | None = Field(
        default=None,
        ge=0.0,
        description="Process creation timestamp in seconds since the UNIX epoch",
    )
    username: str | None = Field(
        default=None,
        description="Username that owns the process (or None if unavailable/restricted)",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Timezone-aware UTC timestamp of process sample",
    )

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None or v.utcoffset() is None:
            raise ValueError("Timestamp must be timezone-aware (UTC)")
        return v


class ProcessCollectionMetrics(BaseModel):
    """Aggregated container for all running system processes."""

    processes: list[ProcessMetrics] = Field(
        default_factory=list,
        description="List of detected processes and their resource utilization",
    )
    total_processes: int = Field(
        ge=0,
        description="Total count of running processes in this snapshot",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Timezone-aware UTC timestamp of process collection snapshot",
    )

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None or v.utcoffset() is None:
            raise ValueError("Timestamp must be timezone-aware (UTC)")
        return v


class SystemMetrics(BaseModel):
    """Top-level container for all operating system performance metrics."""

    cpu: CPUMetrics | None = Field(
        default=None,
        description="CPU telemetry metrics",
    )
    memory: MemoryMetrics | None = Field(
        default=None,
        description="Memory telemetry metrics",
    )
    disk: DiskMetrics | None = Field(
        default=None,
        description="Disk telemetry metrics",
    )
    network: NetworkMetrics | None = Field(
        default=None,
        description="Network telemetry metrics",
    )
    processes: ProcessCollectionMetrics | None = Field(
        default=None,
        description="Running processes telemetry snapshot",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Timezone-aware UTC timestamp of system snapshot",
    )

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None or v.utcoffset() is None:
            raise ValueError("Timestamp must be timezone-aware (UTC)")
        return v
