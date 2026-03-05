"""Latency monitoring for MetaApi operations."""

import time

from app.utils.logger import logger


class LatencyMonitor:
    """Monitor execution latency for operations."""

    def __init__(self, alert_threshold_ms: float = 1000.0):
        """Initialize with alert threshold in milliseconds."""
        self.alert_threshold_ms = alert_threshold_ms
        self.latencies: dict[str, list[float]] = {}
        self._max_samples = 1000

    def measure(self, operation: str):
        """Context manager to measure operation latency."""
        return LatencyContext(self, operation)

    def record(self, operation: str, latency_ms: float):
        """Record a latency measurement."""
        if operation not in self.latencies:
            self.latencies[operation] = []

        self.latencies[operation].append(latency_ms)

        if len(self.latencies[operation]) > self._max_samples:
            self.latencies[operation] = self.latencies[operation][-self._max_samples :]

        if latency_ms > self.alert_threshold_ms:
            logger.warning(
                f"⚠️  HIGH LATENCY: {operation} took {latency_ms:.2f}ms "
                f"(threshold: {self.alert_threshold_ms:.2f}ms)"
            )
        else:
            logger.debug(f"{operation} latency: {latency_ms:.2f}ms")

    def get_stats(self, operation: str) -> dict[str, float] | None:
        """Get latency statistics (mean, min, max, p95, p99)."""
        if operation not in self.latencies or not self.latencies[operation]:
            return None

        latencies = sorted(self.latencies[operation])
        count = len(latencies)

        p95_idx = int(count * 0.95)
        p99_idx = int(count * 0.99)

        return {
            "mean": sum(latencies) / count,
            "min": latencies[0],
            "max": latencies[-1],
            "p95": latencies[p95_idx] if p95_idx < count else latencies[-1],
            "p99": latencies[p99_idx] if p99_idx < count else latencies[-1],
            "count": count,
        }

    def get_all_stats(self) -> dict[str, dict[str, float]]:
        """Get statistics for all monitored operations."""
        return {
            operation: stats
            for operation in self.latencies.keys()
            if (stats := self.get_stats(operation)) is not None
        }

    def reset(self, operation: str | None = None):
        """Reset latency data for an operation or all operations."""
        if operation:
            if operation in self.latencies:
                self.latencies[operation] = []
        else:
            self.latencies = {}

    def log_summary(self):
        """Log a summary of all latency statistics."""
        all_stats = self.get_all_stats()

        if not all_stats:
            logger.info("No latency data recorded")
            return

        logger.info("=== Latency Summary ===")
        for operation, stats in all_stats.items():
            logger.info(
                f"{operation}: "
                f"mean={stats['mean']:.1f}ms, "
                f"p95={stats['p95']:.1f}ms, "
                f"p99={stats['p99']:.1f}ms, "
                f"max={stats['max']:.1f}ms "
                f"(n={stats['count']})"
            )


class LatencyContext:
    """Context manager for measuring operation latency."""

    def __init__(self, monitor: LatencyMonitor, operation: str):
        self.monitor = monitor
        self.operation = operation
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, *args):
        if self.start_time:
            latency_ms = (time.time() - self.start_time) * 1000
            self.monitor.record(self.operation, latency_ms)
