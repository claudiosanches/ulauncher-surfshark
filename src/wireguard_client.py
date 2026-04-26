import os
import subprocess
from typing import Optional
from .vpn_client import VPNClient

class WireGuardClient(VPNClient):
    """VPN client implementation for WireGuard using wg-quick."""

    bin_paths = ["/usr/bin/wg-quick", "/bin/wg-quick", "/usr/sbin/wg-quick"]

    def __init__(self, wireguard_dir_path: str) -> None:
        """
        Initializes the WireGuard client.

        Args:
            wireguard_dir_path: Path where temporary WireGuard configs will be stored.
        """
        self.wireguard_dir_path = wireguard_dir_path
        self.installed_path = self._get_installed_path()

    def _get_installed_path(self) -> Optional[str]:
        """Locates the wg-quick binary on the system."""
        for path in self.bin_paths:
            if os.path.exists(path):
                return path
        return None

    def is_installed(self) -> bool:
        """Checks if wg-quick is installed."""
        return bool(self.installed_path)

    def connect(self, server_profile: str) -> bool:
        """This method is part of VPNClient but we use connect_with_config for dynamic setup."""
        return False

    def connect_with_config(self, iface_name: str, config_content: str) -> bool:
        """
        Connects to a Surfshark server via WireGuard using a dynamic config.

        Args:
            iface_name: The name of the interface (e.g., 'surfshark_wg').
            config_content: The content of the WireGuard configuration file.

        Returns:
            True if initiated, False otherwise.
        """
        if not self.is_installed():
            return False

        config_path = os.path.join(self.wireguard_dir_path, f"{iface_name}.conf")

        # Write config file with 600 permissions
        try:
            with open(config_path, 'w') as f:
                f.write(config_content)
            os.chmod(config_path, 0o600)

            # Bring up the interface
            subprocess.run(["pkexec", self.installed_path, "up", config_path])
            return True
        except Exception:
            return False

    def disconnect(self) -> bool:
        """Disconnects active WireGuard interfaces managed by this extension."""
        if not self.is_installed():
            return False

        try:
            result = subprocess.run(["wg", "show", "interfaces"], capture_output=True, text=True)
            interfaces = result.stdout.strip().split()

            # Our generated configs end with .conf in wireguard_dir_path
            our_profiles = [f[:-5] for f in os.listdir(self.wireguard_dir_path) if f.endswith('.conf')]

            for iface in interfaces:
                if iface in our_profiles:
                    subprocess.run(["pkexec", self.installed_path, "down", os.path.join(self.wireguard_dir_path, f"{iface}.conf")])
            return True
        except Exception:
            return False

    def get_status(self) -> Optional[str]:
        """Checks for active WireGuard interfaces managed by this extension."""
        if not self.is_installed():
            return None

        try:
            result = subprocess.run(["wg", "show", "interfaces"], capture_output=True, text=True)
            output = result.stdout.strip()
            if output:
                interfaces = output.split()
                our_profiles = [f[:-5] for f in os.listdir(self.wireguard_dir_path) if f.endswith('.conf')]

                for iface in interfaces:
                    if iface in our_profiles:
                        return f"{iface}.conf"
        except Exception:
            pass

        return None
