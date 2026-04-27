import os
import subprocess
import re
from typing import Optional, Any
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

    def generate_config(self, privkey: str, pubkey: str, endpoint: str, dns: str = "162.252.172.57, 149.154.159.92") -> str:
        """
        Generates a valid WireGuard configuration string.

        Args:
            privkey: User's private key.
            pubkey: Server's public key.
            endpoint: Server's connection address.
            dns: Comma-separated list of DNS servers.

        Returns:
            The formatted configuration content.
        """
        return f"""[Interface]
PrivateKey = {privkey}
Address = 10.14.0.2/16
DNS = {dns}

[Peer]
PublicKey = {pubkey}
AllowedIPs = 0.0.0.0/0
Endpoint = {endpoint}:51820
"""

    def connect(self, connection_name: str, **kwargs: Any) -> bool:
        """
        Connects to a Surfshark server via WireGuard.

        Args:
            connection_name: The connection name (e.g., 'us-atl.prod.surfshark.com').
            **kwargs: Must contain 'target_server' (dict), 'wg_privkey' (str), and optional 'wg_dns' (str).

        Returns:
            True if initiated, False otherwise.
        """
        if not self.is_installed():
            return False

        target_server = kwargs.get('target_server')
        wg_privkey = kwargs.get('wg_privkey')
        wg_dns = kwargs.get('wg_dns')

        if not target_server or not wg_privkey:
            return False

        iface_name = "surfshark_wg"
        dns_servers = wg_dns if wg_dns else "162.252.172.57, 149.154.159.92"

        config_content = self.generate_config(
            privkey=wg_privkey,
            pubkey=target_server['pubKey'],
            endpoint=target_server['connectionName'],
            dns=dns_servers
        )

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
        """
        Checks for active WireGuard interfaces managed by this extension
        and extracts the connection name from the config file.
        Also verifies if the interface exists in /sys/class/net.
        """
        if not self.is_installed():
            return None

        iface_name = "surfshark_wg"
        if not os.path.exists(f"/sys/class/net/{iface_name}"):
            return None

        try:
            result = subprocess.run(["wg", "show", "interfaces"], capture_output=True, text=True)
            output = result.stdout.strip()
            if output:
                interfaces = output.split()
                # We check each active interface against our known profiles
                for iface in interfaces:
                    config_file = f"{iface}.conf"
                    config_path = os.path.join(self.wireguard_dir_path, config_file)
                    if os.path.exists(config_path):
                        # Extract the actual connection name from the config
                        with open(config_path, 'r') as f:
                            content = f.read()
                            match = re.search(r'Endpoint = (.*?):51820', content)
                            if match:
                                return match.group(1)
                        # Fallback to the interface name if we can't parse it
                        return config_file
        except Exception:
            pass

        return None
