from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ResourceSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ResourceState(str, Enum):
    OPTIMAL = "OPTIMAL"
    NORMAL = "NORMAL"
    ELEVATED = "ELEVATED"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"


class HealthStatus(str, Enum):
    EXCELLENT = "EXCELLENT"
    GOOD = "GOOD"
    DEGRADED = "DEGRADED"
    CRITICAL = "CRITICAL"


class BottleneckType(str, Enum):
    CPU = "CPU"
    MEMORY = "MEMORY"
    DISK = "DISK"
    NETWORK = "NETWORK"


class BottleneckDetection(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: BottleneckType
    severity: ResourceSeverity
    evidence: dict[str, Any] = Field(
        description="Factual measurements and metric values supporting the detection"
    )
    explanation: str = Field(
        description="Detailed explanation of the observed pressure"
    )
    recommended_action: str = Field(
        description="Concrete recommended optimization or remediation action"
    )
    timestamp: datetime = Field(
        description="Timezone-aware UTC timestamp when bottleneck was evaluated"
    )


class ResourceClassification(BaseModel):
    model_config = ConfigDict(extra="ignore")

    status: ResourceState
    utilization_percent: float | None = None
    details: str


class SystemHealthAnalysis(BaseModel):
    model_config = ConfigDict(extra="ignore")

    health_score: int = Field(
        ge=0, le=100, description="Overall system health score (0-100)"
    )
    health_status: HealthStatus = Field(
        description="Aggregated system operational health state"
    )
    cpu_classification: ResourceClassification
    memory_classification: ResourceClassification
    disk_classification: ResourceClassification
    network_classification: ResourceClassification
    warnings: list[str] = Field(default_factory=list)
    critical_alerts: list[str] = Field(default_factory=list)
    suggested_actions: list[str] = Field(default_factory=list)
    active_bottlenecks: list[BottleneckDetection] = Field(default_factory=list)
    timestamp: datetime


class BottlenecksResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    active_bottlenecks: list[BottleneckDetection]
    historical_pressure_detected: bool = Field(
        description="True if sustained resource pressure is evidenced in recent historical records"
    )
    historical_summary: dict[str, Any] | None = None
    timestamp: datetime
