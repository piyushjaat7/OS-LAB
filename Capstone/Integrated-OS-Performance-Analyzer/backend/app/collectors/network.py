import socket
import time
from datetime import UTC, datetime
from typing import Any

import psutil

from app.schemas.metrics import (
    NetworkInterfaceMetrics,
    NetworkIOCountersMetrics,
    NetworkMetrics,
    NetworkThroughputMetrics,
)


class NetworkCollector:
    """Cross-platform collector for network interfaces, cumulative I/O counters, and throughput."""

    def __init__(self) -> None:
        self.initialized_at: datetime = datetime.now(UTC)
        self.last_sampled_at: datetime | None = None
        self._sample_count: int = 0
        self._last_aggregate_time: float | None = None
        self._last_aggregate_io: NetworkIOCountersMetrics | None = None
        self._last_pernic_time: dict[str, float] = {}
        self._last_pernic_io: dict[str, NetworkIOCountersMetrics] = {}

    @staticmethod
    def _to_io_metrics(raw_io: Any) -> NetworkIOCountersMetrics | None:
        """Convert a raw psutil snetio namedtuple into NetworkIOCountersMetrics safely."""
        if raw_io is None:
            return None
        try:
            return NetworkIOCountersMetrics(
                bytes_sent=max(0, int(getattr(raw_io, "bytes_sent", 0))),
                bytes_recv=max(0, int(getattr(raw_io, "bytes_recv", 0))),
                packets_sent=max(0, int(getattr(raw_io, "packets_sent", 0))),
                packets_recv=max(0, int(getattr(raw_io, "packets_recv", 0))),
                errin=max(0, int(getattr(raw_io, "errin", 0))),
                errout=max(0, int(getattr(raw_io, "errout", 0))),
                dropin=max(0, int(getattr(raw_io, "dropin", 0))),
                dropout=max(0, int(getattr(raw_io, "dropout", 0))),
            )
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _extract_safe_addresses(addrs: list[Any] | None) -> list[str] | None:
        """Extract non-sensitive interface address identifiers.

        Omits raw host IP addresses to protect user privacy and avoid leaking
        internal/external network topology, while preserving hardware MAC addresses
        and configured address families (e.g. IPv4, IPv6).
        """
        if not addrs:
            return None

        safe_list: list[str] = []
        seen: set[str] = set()

        for addr in addrs:
            family = getattr(addr, "family", None)
            address = getattr(addr, "address", "") or ""

            # Detect MAC / hardware link layer addresses
            is_mac = False
            fam_name = str(getattr(family, "name", "") or "")
            if (
                "PACKET" in fam_name
                or "LINK" in fam_name
                or (
                    family is not None
                    and getattr(socket, "AF_PACKET", None) is not None
                    and family == socket.AF_PACKET
                )
                or (
                    family is not None
                    and getattr(psutil, "AF_LINK", None) is not None
                    and family == psutil.AF_LINK
                )
            ):
                is_mac = True

            if not is_mac and address:
                parts = address.replace("-", ":").split(":")
                if len(parts) == 6 and all(len(p) <= 2 for p in parts):
                    is_mac = True

            if is_mac and address:
                mac_str = f"MAC: {address}"
                if mac_str not in seen:
                    seen.add(mac_str)
                    safe_list.append(mac_str)
            elif family is not None:
                if "INET6" in fam_name or (
                    getattr(socket, "AF_INET6", None) is not None
                    and family == socket.AF_INET6
                ):
                    label = "IPv6"
                elif "INET" in fam_name or (
                    getattr(socket, "AF_INET", None) is not None
                    and family == socket.AF_INET
                ):
                    label = "IPv4"
                else:
                    label = fam_name if fam_name else str(family)

                if label and label not in seen:
                    seen.add(label)
                    safe_list.append(label)

        return safe_list if safe_list else None

    @staticmethod
    def calculate_rate(
        prev_bytes: int | None,
        curr_bytes: int | None,
        elapsed_seconds: float,
    ) -> float | None:
        """Calculate throughput rate in bytes per second between two consecutive readings.

        Returns None if:
        - Either counter is None (first sample or unavailable).
        - Elapsed time is non-positive (zero or negative interval).
        - Counter reset or rollover occurred (curr_bytes < prev_bytes).
        """
        if prev_bytes is None or curr_bytes is None:
            return None
        if elapsed_seconds <= 0.0:
            return None
        delta = curr_bytes - prev_bytes
        if delta < 0:
            return None
        return round(float(delta / elapsed_seconds), 2)

    @classmethod
    def calculate_throughput(
        cls,
        prev_io: NetworkIOCountersMetrics | None,
        curr_io: NetworkIOCountersMetrics | None,
        elapsed_seconds: float,
    ) -> NetworkThroughputMetrics | None:
        """Calculate upload and download throughput from two cumulative counter snapshots.

        Returns None if current I/O counters are unavailable.
        Returns a throughput model with None fields if no baseline exists (first sample)
        or elapsed time is non-positive.
        """
        if curr_io is None:
            return None
        if prev_io is None or elapsed_seconds <= 0.0:
            return NetworkThroughputMetrics(
                bytes_sent_per_sec=None,
                bytes_recv_per_sec=None,
            )

        sent_rate = cls.calculate_rate(
            prev_io.bytes_sent, curr_io.bytes_sent, elapsed_seconds
        )
        recv_rate = cls.calculate_rate(
            prev_io.bytes_recv, curr_io.bytes_recv, elapsed_seconds
        )
        return NetworkThroughputMetrics(
            bytes_sent_per_sec=sent_rate,
            bytes_recv_per_sec=recv_rate,
        )

    def _collect_interfaces(self, now_time: float) -> list[NetworkInterfaceMetrics]:
        """Internal helper to discover network interfaces, populate metadata, and compute per-NIC throughput.

        Interface Filtering Strategy:
        All legitimate named network interfaces reported by the kernel/psutil
        (including physical, wireless, virtual, bridge, and loopback interfaces)
        are preserved without silent dropping. Only null, empty, or whitespace-only
        interface names are filtered out. Discovered interfaces are deterministically
        sorted by interface identifier.
        """
        try:
            stats_dict = psutil.net_if_stats() or {}
        except (psutil.Error, OSError):
            stats_dict = {}

        try:
            pernic_io = psutil.net_io_counters(pernic=True) or {}
        except (psutil.Error, OSError):
            pernic_io = {}

        try:
            addrs_dict = psutil.net_if_addrs() or {}
        except (psutil.Error, OSError, AttributeError):
            addrs_dict = {}

        all_names = sorted(
            {
                name.strip()
                for name in (set(stats_dict.keys()) | set(pernic_io.keys()))
                if name and name.strip()
            }
        )

        current_interface_set = set(all_names)

        # Handle interface disappearance: clean up stale cached baselines
        disappeared = set(self._last_pernic_io.keys()) - current_interface_set
        for d in disappeared:
            self._last_pernic_io.pop(d, None)
            self._last_pernic_time.pop(d, None)

        interfaces: list[NetworkInterfaceMetrics] = []
        for name in all_names:
            stats = stats_dict.get(name)
            is_up = bool(getattr(stats, "isup", False)) if stats is not None else False
            speed_raw = getattr(stats, "speed", None) if stats is not None else None
            speed = int(speed_raw) if speed_raw is not None and speed_raw > 0 else None
            mtu_raw = getattr(stats, "mtu", None) if stats is not None else None
            mtu = int(mtu_raw) if mtu_raw is not None and mtu_raw > 0 else None

            addresses = self._extract_safe_addresses(addrs_dict.get(name))

            raw_nic_io = pernic_io.get(name)
            nic_io = self._to_io_metrics(raw_nic_io) if raw_nic_io is not None else None

            if nic_io is not None:
                if name in self._last_pernic_io and name in self._last_pernic_time:
                    prev_nic_io = self._last_pernic_io[name]
                    elapsed_nic = now_time - self._last_pernic_time[name]
                    nic_throughput = self.calculate_throughput(
                        prev_nic_io, nic_io, elapsed_nic
                    )
                else:
                    nic_throughput = NetworkThroughputMetrics(
                        bytes_sent_per_sec=None,
                        bytes_recv_per_sec=None,
                    )
                self._last_pernic_io[name] = nic_io
                self._last_pernic_time[name] = now_time
            else:
                nic_throughput = None

            interfaces.append(
                NetworkInterfaceMetrics(
                    name=name,
                    is_up=is_up,
                    speed=speed,
                    mtu=mtu,
                    addresses=addresses,
                    io_counters=nic_io,
                    throughput=nic_throughput,
                )
            )

        return interfaces

    def get_network_io_counters(self) -> NetworkIOCountersMetrics | None:
        """Collect system-wide cumulative network I/O counters.

        Returns:
            NetworkIOCountersMetrics | None: System-wide cumulative I/O counters, or None if unavailable.
        """
        now = datetime.now(UTC)
        try:
            raw_io = psutil.net_io_counters()
            counters = self._to_io_metrics(raw_io)
        except (psutil.Error, OSError):
            counters = None

        self.last_sampled_at = now
        self._sample_count += 1
        return counters

    def get_network_interfaces(self) -> list[NetworkInterfaceMetrics]:
        """Collect and return list of detected network interfaces and their metrics.

        Returns:
            list[NetworkInterfaceMetrics]: Discovered interfaces with metadata, I/O counters, and throughput.
        """
        now_dt = datetime.now(UTC)
        now_time = time.monotonic()
        interfaces = self._collect_interfaces(now_time)
        self.last_sampled_at = now_dt
        self._sample_count += 1
        return interfaces

    def get_network_metrics(self) -> NetworkMetrics:
        """Collect unified network snapshot with interfaces, aggregate counters, and throughput.

        Returns:
            NetworkMetrics: Combined network telemetry model with a shared UTC timestamp.
        """
        now_dt = datetime.now(UTC)
        now_time = time.monotonic()

        try:
            raw_agg_io = psutil.net_io_counters()
            agg_io = self._to_io_metrics(raw_agg_io)
        except (psutil.Error, OSError):
            agg_io = None

        if agg_io is not None:
            if (
                self._last_aggregate_time is not None
                and self._last_aggregate_io is not None
            ):
                elapsed_agg = now_time - self._last_aggregate_time
                agg_throughput = self.calculate_throughput(
                    self._last_aggregate_io, agg_io, elapsed_agg
                )
            else:
                agg_throughput = NetworkThroughputMetrics(
                    bytes_sent_per_sec=None,
                    bytes_recv_per_sec=None,
                )
            self._last_aggregate_io = agg_io
            self._last_aggregate_time = now_time
        else:
            agg_throughput = None

        interfaces = self._collect_interfaces(now_time)

        self.last_sampled_at = now_dt
        self._sample_count += 1

        return NetworkMetrics(
            interfaces=interfaces,
            io_counters=agg_io,
            throughput=agg_throughput,
            timestamp=now_dt,
        )
