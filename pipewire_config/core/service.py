"""WirePlumber service lifecycle manager."""

import time
import subprocess
from typing import Tuple


def restart_wireplumber(timeout: int = 10, wait_delay: float = 2.0) -> Tuple[bool, str]:
    """
    Restart the user WirePlumber systemd service.
    Returns (success: bool, message: str).
    """
    try:
        result = subprocess.run(
            ['systemctl', '--user', 'restart', 'wireplumber'],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        if result.returncode == 0:
            if wait_delay > 0:
                time.sleep(wait_delay)
            return True, "WirePlumber has been restarted successfully!"
        else:
            return False, f"Failed to restart WirePlumber:\n\n{result.stderr}"
    except subprocess.TimeoutExpired:
        return False, "Restart command timed out.\n\nTry manually: systemctl --user restart wireplumber"
    except FileNotFoundError:
        return False, "systemctl command not found. Ensure systemd is installed."
    except Exception as e:
        return False, f"Failed to restart WirePlumber:\n\n{str(e)}"
