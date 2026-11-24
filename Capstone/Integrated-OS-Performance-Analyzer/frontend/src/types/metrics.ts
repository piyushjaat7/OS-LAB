export interface CPUFrequency {
  current: number;
  min: number | null;
  max: number | null;
}

export interface CPUMetrics {
  usage_percent: number | null;
  per_core_usage: (number | null)[] | null;
  physical_cores: number | null;
  logical_cores: number | null;
  frequency: CPUFrequency | null;
  timestamp: string;
}

export interface VirtualMemoryMetrics {
  total: number;
  available: number;
  percent: number;
  used: number;
  free: number;
}

export interface SwapMemoryMetrics {
  total: number;
  used: number;
  free: number;
  percent: number;
  sin: number;
  sout: number;
}

export interface MemoryMetrics {
  virtual: VirtualMemoryMetrics;
  swap: SwapMemoryMetrics;
  timestamp: string;
}

export interface DiskUsageMetrics {
  total: number;
  used: number;
  free: number;
  percent: number;
}

export interface DiskPartitionMetrics {
  device: string;
  mountpoint: string;
  filesystem: string;
  options: string;
  mountpoints?: string[];
}

export interface DiskIOCountersMetrics {
  read_count: number;
  write_count: number;
  read_bytes: number;
  write_bytes: number;
  read_time: number;
  write_time: number;
}

export interface DiskPartitionInfo {
  partition: DiskPartitionMetrics;
  usage: DiskUsageMetrics | null;
}

export interface DiskMetrics {
  partitions: DiskPartitionInfo[];
  io_counters: DiskIOCountersMetrics | null;
  total_capacity_bytes?: number | null;
  total_used_bytes?: number | null;
  total_free_bytes?: number | null;
  total_percent?: number | null;
  unique_partition_count?: number | null;
  timestamp: string;
}

export interface NetworkIOCountersMetrics {
  bytes_sent: number;
  bytes_recv: number;
  packets_sent: number;
  packets_recv: number;
  errin: number;
  errout: number;
  dropin: number;
  dropout: number;
}

export interface NetworkThroughputMetrics {
  bytes_sent_per_sec: number | null;
  bytes_recv_per_sec: number | null;
}

export interface NetworkInterfaceMetrics {
  name: string;
  is_up: boolean;
  speed: number | null;
  mtu: number | null;
  addresses: string[] | null;
  io_counters: NetworkIOCountersMetrics | null;
  throughput: NetworkThroughputMetrics | null;
}

export interface NetworkMetrics {
  interfaces: NetworkInterfaceMetrics[];
  io_counters: NetworkIOCountersMetrics | null;
  throughput: NetworkThroughputMetrics | null;
  timestamp: string;
}

export interface ProcessMetrics {
  pid: number;
  name: string;
  status: string;
  cpu_percent: number | null;
  memory_rss: number;
  memory_vms: number;
  memory_percent: number;
  num_threads: number;
  create_time: number;
  username: string | null;
}

export interface ProcessCollectionMetrics {
  processes: ProcessMetrics[];
  total_processes: number;
  timestamp: string;
}

export interface SystemMetrics {
  cpu: CPUMetrics | null;
  memory: MemoryMetrics | null;
  disk: DiskMetrics | null;
  network: NetworkMetrics | null;
  processes: ProcessCollectionMetrics | null;
  timestamp: string;
}

export interface HistoricalCPUInfo {
  usage_percent: number | null;
  per_core_usage: (number | null)[] | null;
  physical_cores: number | null;
  logical_cores: number | null;
  frequency_mhz: number | null;
}

export interface HistoricalMemoryInfo {
  total_bytes: number | null;
  used_bytes: number | null;
  available_bytes: number | null;
  percent: number | null;
  swap_total_bytes: number | null;
  swap_used_bytes: number | null;
  swap_percent: number | null;
}

export interface HistoricalDiskInfo {
  total_bytes: number | null;
  used_bytes: number | null;
  free_bytes: number | null;
  percent: number | null;
  read_bytes: number | null;
  write_bytes: number | null;
  read_count: number | null;
  write_count: number | null;
}

export interface HistoricalNetworkInfo {
  bytes_sent: number | null;
  bytes_recv: number | null;
  packets_sent: number | null;
  packets_recv: number | null;
  throughput_sent_bytes_per_sec: number | null;
  throughput_recv_bytes_per_sec: number | null;
}

export interface HistoricalSystemMetrics {
  id: string | null;
  timestamp: string;
  cpu: HistoricalCPUInfo | null;
  memory: HistoricalMemoryInfo | null;
  disk: HistoricalDiskInfo | null;
  network: HistoricalNetworkInfo | null;
  total_processes: number | null;
}

export interface HistoricalMetricsSummary {
  sample_count: number;
  start_time: string | null;
  end_time: string | null;
  cpu_avg_percent: number | null;
  cpu_max_percent: number | null;
  memory_avg_percent: number | null;
  memory_max_percent: number | null;
  network_avg_bytes_sent_per_sec: number | null;
  network_avg_bytes_recv_per_sec: number | null;
}

export interface HealthResponse {
  status: string;
  database: string;
}

export interface ThresholdSettings {
  cpuWarning: number;
  cpuCritical: number;
  memoryWarning: number;
  memoryCritical: number;
  diskWarning: number;
  diskCritical: number;
  chartHistoryLength: number;
  streamInterval: number;
}

// Phase 5: Analysis and Scheduling types
export type ResourceSeverity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type ResourceState = 'OPTIMAL' | 'NORMAL' | 'ELEVATED' | 'WARNING' | 'CRITICAL' | 'UNKNOWN';
export type HealthStatus = 'EXCELLENT' | 'GOOD' | 'DEGRADED' | 'CRITICAL';
export type BottleneckType = 'CPU' | 'MEMORY' | 'DISK' | 'NETWORK';

export interface BottleneckDetection {
  type: BottleneckType;
  severity: ResourceSeverity;
  evidence: Record<string, any>;
  explanation: string;
  recommended_action: string;
  timestamp: string;
}

export interface ResourceClassification {
  status: ResourceState;
  utilization_percent: number | null;
  details: string;
}

export interface SystemHealthAnalysis {
  health_score: number;
  health_status: HealthStatus;
  cpu_classification: ResourceClassification;
  memory_classification: ResourceClassification;
  disk_classification: ResourceClassification;
  network_classification: ResourceClassification;
  warnings: string[];
  critical_alerts: string[];
  suggested_actions: string[];
  active_bottlenecks: BottleneckDetection[];
  timestamp: string;
}

export interface BottlenecksResponse {
  active_bottlenecks: BottleneckDetection[];
  historical_pressure_detected: boolean;
  historical_summary: Record<string, any> | null;
  timestamp: string;
}

export interface ProcessWorkload {
  process_id: string;
  arrival_time: number;
  burst_time: number;
  priority?: number;
}

export interface GanttSegment {
  process_id: string;
  start_time: number;
  end_time: number;
  duration: number;
}

export interface ProcessSimulationMetric {
  process_id: string;
  arrival_time: number;
  burst_time: number;
  priority: number;
  completion_time: number;
  turnaround_time: number;
  waiting_time: number;
  response_time: number;
}

export interface SimulationResult {
  algorithm: string;
  mode: string | null;
  time_quantum: number | null;
  priority_order: string | null;
  processes: ProcessSimulationMetric[];
  gantt_chart: GanttSegment[];
  total_simulation_time: number;
  idle_time: number;
  cpu_utilization_percent: number;
  throughput: number;
  avg_waiting_time: number;
  avg_turnaround_time: number;
  avg_response_time: number;
}

export interface AlgorithmSummary {
  algorithm: string;
  mode: string | null;
  avg_waiting_time: number;
  avg_turnaround_time: number;
  avg_response_time: number;
  cpu_utilization_percent: number;
  throughput: number;
}

export interface SchedulingComparison {
  workload_size: number;
  algorithms: Record<string, SimulationResult>;
  summary_table: AlgorithmSummary[];
  workload_analysis: string;
}
