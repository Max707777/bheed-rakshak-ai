import requests
import config


class ESP32Controller:
    """Dispatches crowd intervention decisions to ESP32 hardware via HTTP GET."""

    def __init__(self):
        """Initialize controller with state tracking for change detection."""
        self.last_dispatched_action = None
        self.last_status = "IDLE"

    def send_command(self, action):
        """Send HTTP GET to ESP32 only when action changes, logging failures safely."""
        mode = getattr(config, "MODE", getattr(config, "ESP32_MODE", "simulated"))

        if mode == "simulated":
            self.last_status = f"SIMULATED: {action}"
            return True, f"SIMULATED: {action}"

        # Only dispatch when action changes
        if action == self.last_dispatched_action:
            return True, f"CACHED: {action}"

        esp32_ip = getattr(config, "ESP32_IP", "192.168.1.50")
        url = f"http://{esp32_ip}/command?action={action}"

        try:
            response = requests.get(url, timeout=2.0)
            if response.status_code == 200:
                self.last_dispatched_action = action
                self.last_status = f"SENT: {action}"
                print(f"[ESP32] Successfully dispatched: {action} -> {url}")
                return True, url
            else:
                self.last_status = f"HTTP {response.status_code}: {action}"
                print(f"[ESP32 WARN] Unexpected response {response.status_code} for {url}")
                return False, url
        except Exception as e:
            self.last_status = f"ERR: {action}"
            print(f"[ESP32 ERROR] Dispatch failed ({action}): {e}")
            return False, url
