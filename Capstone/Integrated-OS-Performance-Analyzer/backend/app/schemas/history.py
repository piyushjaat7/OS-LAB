from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class HistoricalCPUInfo(BaseModel):
    """Historical CPU telemetry model."""

    model_config = ConfigDict(extra="ignore")

    usage_percent: float | None = Field(
        default=None,
        description="Overall CPU utilization percentage",
    )
    per_core_usage: list[float | None] | None = Field(
        default=None,
        description="Per-logical-core CPU utilization percentage",
    )
    physical_cores: int | None = Field(
        default=None,
        description="Number of physical CPU cores",
    )
    logical_cores: int | None = Field(
        default=None,
        description="Number of logical CPU cores",
    )
    frequency_mhz: float | None = Field(
        default=None,
        description="Current CPU operating frequency in MHz",
    )


class HistoricalMemoryInfo(BaseModel):
    """Historical virtual and swap memory metrics model."""

    model_config = ConfigDict(extra="ignore")

    total_bytes: int | None = Field(
        default=None,
        description="Total physical RAM in bytes",
    )
    used_bytes: int | None = Field(
        default=None,
        description="Used physical RAM in bytes",
    )
    available_bytes: int | None = Field(
        default=None,
        description="Available physical RAM in bytes",
    )
    percent: float | None = Field(
        default=None,
        description="Physical RAM utilization percentage",
    )
    swap_total_bytes: int | None = Field(
        default=None,
        description="Total swap memory in bytes",
    )
    swap_used_bytes: int | None = Field(
        default=None,
        description="Used swap memory in bytes",
    )
    swap_percent: float | None = Field(
        default=None,
        description="Swap memory utilization percentage",
    )


class HistoricalDiskInfo(BaseModel):
    """Historical storage capacity and aggregate I/O counters model."""

    model_config = ConfigDict(extra="ignore")

    total_bytes: int | None = Field(
        default=None,
        description="Aggregate disk capacity across partitions in bytes",
    )
    used_bytes: int | None = Field(
        default=None,
        description="Aggregate used disk space across partitions in bytes",
    )
    free_bytes: int | None = Field(
        default=None,
        description="Aggregate free disk space across partitions in bytes",
    )
    percent: float | None = Field(
        default=None,
        description="Aggregate disk utilization percentage",
    )
    read_bytes: int | None = Field(
        default=None,
        description="Cumulative disk read bytes",
    )
    write_bytes: int | None = Field(
        default=None,
        description="Cumulative disk write bytes",
    )
    read_count: int | None = Field(
        default=None,
        description="Cumulative disk read operations count",
    )
    write_count: int | None = Field(
        default=None,
        description="Cumulative disk write operations count",
    )


class HistoricalNetworkInfo(BaseModel):
    """Historical network traffic counters and throughput model."""

    model_config = ConfigDict(extra="ignore")

    bytes_sent: int | None = Field(
        default=None,
        description="Cumulative bytes transmitted",
    )
    bytes_recv: int | None = Field(
        default=None,
        description="Cumulative bytes received",
    )
    packets_sent: int | None = Field(
        default=None,
        description="Cumulative packets transmitted",
    )
    packets_recv: int | None = Field(
        default=None,
        description="Cumulative packets received",
    )
    throughput_sent_bytes_per_sec: float | None = Field(
        default=None,
        description="Network transmission throughput in bytes per second",
    )
    throughput_recv_bytes_per_sec: float | None = Field(
        default=None,
        description="Network reception throughput in bytes per second",
    )


class HistoricalSystemMetrics(BaseModel):
    """Historical unified system metrics document model stored in MongoDB."""

    model_config = ConfigDict(extra="ignore")

    id: str | None = Field(
        default=None,
        description="Hex string representation of MongoDB ObjectId",
    )
    timestamp: datetime = Field(
        description="Timezone-aware UTC timestamp when metrics snapshot was collected",
    )
    cpu: HistoricalCPUInfo | None = None
    memory: HistoricalMemoryInfo | None = None
    disk: HistoricalDiskInfo | None = None
    network: HistoricalNetworkInfo | None = None
    total_processes: int | None = Field(
        default=None,
        description="Total active system processes count (individual process list omitted)",
    )


class HistoricalMetricsSummary(BaseModel):
    """Aggregated historical system telemetry statistics for a query time range."""

    model_config = ConfigDict(extra="ignore")

    sample_count: int = Field(
        description="Number of historical metric samples included in aggregate",
    )
    start_time: datetime | None = Field(
        default=None,
        description="Earliest sample timestamp in aggregated window",
    )
    end_time: datetime | None = Field(
        default=None,
        description="Latest sample timestamp in aggregated window",
    )
    cpu_avg_percent: float | None = Field(
        default=None,
        description="Average CPU utilization percentage",
    )
    cpu_max_percent: float | None = Field(
        default=None,
        description="Maximum CPU utilization percentage",
    )
    memory_avg_percent: float | None = Field(
        default=None,
        description="Average virtual RAM utilization percentage",
    )
    memory_max_percent: float | None = Field(
        default=None,
        description="Maximum virtual RAM utilization percentage",
    )
    network_avg_bytes_sent_per_sec: float | None = Field(
        default=None,
        description="Average network transmission rate in bytes per second",
    )
    network_avg_bytes_recv_per_sec: float | None = Field(
        default=None,
        description="Average network reception rate in bytes per second",
    )
