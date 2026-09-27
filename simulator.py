import config


class ScenarioSimulator:
    """Evaluates exit-state scenarios to recommend crowd management interventions."""

    def __init__(self, exit_throughput=None):
        """Initialize simulator with exit throughput assumptions."""
        self.throughput = exit_throughput if exit_throughput is not None else config.EXIT_THROUGHPUT

    def simulate(self, current_count, inflow_rate, critical_threshold):
        """Evaluate hypothetical exit scenarios and return the recommended action with metrics."""
        results = {}
        for action, outflow_rate in self.throughput.items():
            net_rate = inflow_rate - outflow_rate
            if net_rate > 0.01 and current_count < critical_threshold:
                time_to_crit = (critical_threshold - current_count) / net_rate
            else:
                time_to_crit = float("inf")  # safe / stabilizing
            results[action] = {
                "outflow": outflow_rate,
                "net_rate": net_rate,
                "time_to_critical": time_to_crit
            }

        # If already safe or count is small, remain NORMAL
        if current_count < (critical_threshold * 0.5) and inflow_rate <= self.throughput["NORMAL"]:
            best_action = "NORMAL"
        else:
            # Find the minimal intervention that keeps net_rate <= 0 or maximizes time_to_critical
            safe_actions = [a for a in ["NORMAL", "OPEN_EXIT_1", "OPEN_EXIT_2", "OPEN_ALL_EXITS"]
                            if a in results and results[a]["net_rate"] <= 0]
            if safe_actions:
                best_action = safe_actions[0]
            else:
                best_action = "OPEN_ALL_EXITS"

        return best_action, results
