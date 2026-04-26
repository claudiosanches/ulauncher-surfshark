import os
import subprocess
import re
from typing import Optional, Any
from .vpn_client import VPNClient

class OpenVPNClient(VPNClient):
    """VPN client implementation for OpenVPN."""

    bin_paths = ["/usr/bin/openvpn", "/bin/openvpn", "/usr/sbin/openvpn"]

    def __init__(self, surfshark_dir_path: str, config_file_path: str) -> None:
        """
        Initializes the OpenVPN client.

        Args:
            surfshark_dir_path: Path to the directory containing OpenVPN profiles.
            config_file_path: Path to the service credentials configuration file.
        """
        self.surfshark_dir_path = surfshark_dir_path
        self.config_file_path = config_file_path
        self.installed_path = self._get_installed_path()

    def _get_installed_path(self) -> Optional[str]:
        """
        Locates the OpenVPN binary on the system.

        Returns:
            The absolute path to the binary if found, None otherwise.
        """
        for path in self.bin_paths:
            if os.path.exists(path):
                return path
        return None

    def is_installed(self) -> bool:
        """Checks if OpenVPN is installed."""
        return bool(self.installed_path)

    def connect(self, server_profile: str, **kwargs: Any) -> bool:
        """
        Connects to a Surfshark server via OpenVPN.

        Args:
            server_profile: The filename of the .ovpn profile.
            **kwargs: Unused in this implementation.

        Returns:
            True if initiated, False otherwise.
        """
        if not self.is_installed():
            return False

        # Need to run command in new bash and background to avoid locking extension
        cmd = ["pkexec", "bash", "-lc", f"{self.installed_path} --config {self.surfshark_dir_path}/{server_profile} --auth-user-pass {self.config_file_path} &"]
        subprocess.run(cmd)
        return True

    def disconnect(self) -> bool:
        """
        Disconnects the active OpenVPN session by killing the process.

        Returns:
            True if the kill command was sent, False otherwise.
        """
        if not self.is_installed():
            return False

        try:
            pgrep = subprocess.run(["pgrep", "-f", f"{self.installed_path} --config"], capture_output=True, text=True)
            pids = pgrep.stdout.strip().split()
            if pids:
                subprocess.run(["pkexec", "kill"] + pids)
            return True
        except Exception:
            return False

    def get_status(self) -> Optional[str]:
        """
        Checks if an OpenVPN process is running and extracts the profile name.

        Returns:
            The filename of the connected .ovpn profile if active, None otherwise.
        """
        if not self.is_installed():
            return None

        try:
            pgrep = subprocess.run(["pgrep", "-af", f"{self.installed_path} --config"], capture_output=True, text=True)
            output = pgrep.stdout
            if output:
                match = re.search(r'--config\s+(.*?\.ovpn)', output)
                if match:
                    return os.path.basename(match.group(1))
        except Exception:
            pass

        return None
