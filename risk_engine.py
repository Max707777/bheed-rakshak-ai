import config


class RiskEngine:
    """Evaluates crowd density risk levels for each zone."""

    def __init__(self, thresholds=None):
        """Initialize risk engine with count thresholds per zone."""
        self.thresholds = thresholds if thresholds is not None else config.RISK_THRESHOLDS

    def evaluate_zone(self, zone_name, count):
        """Return risk state ('NORMAL', 'WARNING', 'HIGH', 'CRITICAL') for a zone count."""
        zone_thresh = self.thresholds.get(zone_name, {"WARNING": 3, "HIGH": 6, "CRITICAL": 10})
        if count >= zone_thresh["CRITICAL"]:
            return "CRITICAL"
        elif count >= zone_thresh["HIGH"]:
            return "HIGH"
        elif count >= zone_thresh["WARNING"]:
            return "WARNING"
        return "NORMAL"

    def get_color(self, risk_state):
        """Return BGR color tuple corresponding to the risk state."""
        return config.RISK_COLORS.get(risk_state, (0, 255, 0))
