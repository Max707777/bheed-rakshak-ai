import time
from collections import deque
import config


class CrowdPredictor:
    """Predicts crowd rate of change and time-to-critical based on rolling count history."""

    def __init__(self, window_seconds=config.HISTORY_WINDOW_SECONDS):
        """Initialize rolling time window buffer for count timestamps."""
        self.window_seconds = window_seconds
        self.history = {}

    def update(self, zone_name, count):
        """Record count at current timestamp for a zone and purge old records."""
        now = time.time()
        if zone_name not in self.history:
            self.history[zone_name] = deque()
        self.history[zone_name].append((now, count))
        while self.history[zone_name] and (now - self.history[zone_name][0][0] > self.window_seconds):
            self.history[zone_name].popleft()

    def predict(self, zone_name, critical_threshold):
        """Compute rate of change and estimated seconds until critical threshold is reached."""
        records = self.history.get(zone_name, [])
        if len(records) < 2:
            return 0.0, None
        t_first, c_first = records[0]
        t_last, c_last = records[-1]
        dt = t_last - t_first
        if dt <= 0.2:
            return 0.0, None
        rate_of_change = (c_last - c_first) / dt
        if rate_of_change > 0.01 and c_last < critical_threshold:
            time_to_critical = (critical_threshold - c_last) / rate_of_change
        else:
            time_to_critical = None
        return rate_of_change, time_to_critical
