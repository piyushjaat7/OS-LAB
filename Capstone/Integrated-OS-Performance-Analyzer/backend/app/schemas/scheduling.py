from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProcessWorkload(BaseModel):
    model_config = ConfigDict(extra="ignore")

    process_id: str = Field(description="Unique process identifier (e.g. 'P1', 'P2')")
    arrival_time: float = Field(
        ge=0.0, description="Arrival time in ready queue (>= 0)"
    )
    burst_time: float = Field(gt=0.0, description="CPU burst time required (> 0)")
    priority: int = Field(default=0, description="Process priority level")


class SchedulingRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    processes: list[ProcessWorkload] = Field(
        min_length=1, description="List of simulated processes to schedule"
    )

    @field_validator("processes")
    @classmethod
    def validate_unique_process_ids(
        cls, v: list[ProcessWorkload]
    ) -> list[ProcessWorkload]:
        seen = set()
        for p in v:
            if p.process_id in seen:
                raise ValueError(
                    f"Duplicate process_id detected: '{p.process_id}'. Each process must have a unique identifier."
                )
            seen.add(p.process_id)
        return v


class PrioritySchedulingRequest(SchedulingRequest):
    preemptive: bool = Field(
        default=False, description="Enable preemptive priority scheduling"
    )
    priority_order: str = Field(
        default="lower_is_higher",
        pattern="^(lower_is_higher|higher_is_higher)$",
        description="Priority interpretation convention (default: lower number = higher priority)",
    )


class RoundRobinSchedulingRequest(SchedulingRequest):
    time_quantum: float = Field(
        default=2.0,
        gt=0.0,
        description="Time quantum slice for round robin scheduling (> 0)",
    )


class CompareSchedulingRequest(SchedulingRequest):
    time_quantum: float = Field(
        default=2.0, gt=0.0, description="Time quantum for Round Robin comparison"
    )
    priority_order: str = Field(
        default="lower_is_higher",
        pattern="^(lower_is_higher|higher_is_higher)$",
        description="Priority convention for priority scheduling comparison",
    )


class GanttSegment(BaseModel):
    model_config = ConfigDict(extra="ignore")

    process_id: str = Field(description="Scheduled process identifier or 'IDLE'")
    start_time: float = Field(description="Segment start time")
    end_time: float = Field(description="Segment end time")
    duration: float = Field(description="Segment execution duration")


class ProcessSimulationMetric(BaseModel):
    model_config = ConfigDict(extra="ignore")

    process_id: str
    arrival_time: float
    burst_time: float
    priority: int
    completion_time: float = Field(description="Time when process completed execution")
    turnaround_time: float = Field(
        description="Total time from arrival to completion (CT - AT)"
    )
    waiting_time: float = Field(
        description="Total time spent waiting in ready queue (TAT - BT)"
    )
    response_time: float = Field(
        description="Time from arrival to first execution start"
    )


class SimulationResult(BaseModel):
    model_config = ConfigDict(extra="ignore")

    algorithm: str = Field(description="Scheduling algorithm name")
    mode: str | None = Field(
        default=None, description="Preemption mode (if applicable)"
    )
    time_quantum: float | None = Field(
        default=None, description="Time quantum (if applicable)"
    )
    priority_order: str | None = Field(
        default=None, description="Priority convention (if applicable)"
    )
    processes: list[ProcessSimulationMetric]
    gantt_chart: list[GanttSegment]
    total_simulation_time: float = Field(
        description="Total wall-clock duration of simulation"
    )
    idle_time: float = Field(description="Total CPU idle duration")
    cpu_utilization_percent: float = Field(
        description="Percentage of simulation time CPU was busy"
    )
    throughput: float = Field(description="Number of completed processes per unit time")
    avg_waiting_time: float = Field(
        description="Average waiting time across all processes"
    )
    avg_turnaround_time: float = Field(
        description="Average turnaround time across all processes"
    )
    avg_response_time: float = Field(
        description="Average response time across all processes"
    )


class AlgorithmSummary(BaseModel):
    model_config = ConfigDict(extra="ignore")

    algorithm: str
    mode: str | None = None
    avg_waiting_time: float
    avg_turnaround_time: float
    avg_response_time: float
    cpu_utilization_percent: float
    throughput: float


class SchedulingComparison(BaseModel):
    model_config = ConfigDict(extra="ignore")

    workload_size: int
    algorithms: dict[str, SimulationResult]
    summary_table: list[AlgorithmSummary]
    workload_analysis: str = Field(
        description="Analytical summary explaining trade-offs across algorithms for this workload"
    )
