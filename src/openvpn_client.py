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
        self.dns_script_path = os.path.join(self.surfshark_dir_path, "update-dns.sh")
        self._create_dns_script()

    def _create_dns_script(self) -> None:
        """Creates a helper script to update DNS settings via resolvectl or resolvconf."""
        script_content = """#!/bin/bash
# DNS Update Script for OpenVPN

DNS_SERVERS=()
for opt in ${!foreign_option_*}; do
    val=${!opt}
    if [[ "$val" == *"dhcp-option DNS "* ]]; then
        DNS_SERVERS+=("${val#*dhcp-option DNS }")
    fi
done

if [[ "$script_type" == "up" ]]; then
    if command -v resolvectl &> /dev/null; then
        resolvectl dns "$dev" "${DNS_SERVERS[@]}"
        resolvectl domain "$dev" "~."
        resolvectl default-route "$dev" yes
    elif command -v resolvconf &> /dev/null; then
        for dns in "${DNS_SERVERS[@]}"; do
            echo "nameserver $dns"
        done | resolvconf -a "$dev.openvpn"
    fi
elif [[ "$script_type" == "down" ]]; then
    if command -v resolvectl &> /dev/null; then
        resolvectl revert "$dev"
    elif command -v resolvconf &> /dev/null; then
        resolvconf -d "$dev.openvpn"
    fi
fi
"""
        try:
            with open(self.dns_script_path, 'w') as f:
                f.write(script_content)
            os.chmod(self.dns_script_path, 0o755)
        except Exception:
            pass

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

    def _ensure_profile_exists(self, server_profile: str) -> bool:
        """Checks if a profile exists and modernizes it if necessary."""
        target_path = os.path.join(self.surfshark_dir_path, server_profile)
        
        # Extract protocol and check if multi-hop
        match_p = re.search(r'_(udp|tcp)\.ovpn$', server_profile)
        proto = match_p.group(1) if match_p else "udp"
        is_multihop = 'mp0' in server_profile

        # If it exists, check if it needs modernization or port fix
        if os.path.exists(target_path):
            with open(target_path, 'r') as f:
                content = f.read()
            
            # Multi-hop needs port 443 for TCP
            # Multi-hop needs port 443 for BOTH TCP and UDP
            needs_port_fix = is_multihop and " 443" not in content
            
            if 'data-ciphers' in content and 'pull-filter ignore' in content and not needs_port_fix:
                return True
            
            # Modernize/Fix in-place
            try:
                if needs_port_fix:
                    new_remote_base = server_profile.replace("_tcp.ovpn", "").replace("_udp.ovpn", "")
                    content = re.sub(r'remote .*? \d+', f'remote {new_remote_base} 443', content)

                if proto == "tcp":
                    content = re.sub(r'^(fast-io|explicit-exit-notify)', r'#\1', content, flags=re.MULTILINE)
                
                if 'pull-filter ignore' not in content:
                    content += "\npull-filter ignore \"explicit-exit-notify\""
                    content += "\npull-filter ignore \"block-outside-dns\""

                if 'data-ciphers ' not in content:
                    content = re.sub(r'^cipher .*', 'data-ciphers AES-256-GCM:AES-128-GCM:CHACHA20-POLY1305\ncipher AES-256-GCM', content, flags=re.MULTILINE)

                if 'remote-cert-tls server' not in content:
                    content += "\nremote-cert-tls server"

                with open(target_path, 'w') as f:
                    f.write(content)
                return True
            except Exception:
                return True

        # File doesn't exist, we need to generate it from a template
        match_gen = re.match(r'(.*)_(udp|tcp)\.ovpn', server_profile)
        if not match_gen:
            return False

        new_remote = match_gen.group(1)
        new_proto = match_gen.group(2)
        
        # Multi-hop uses 443 for BOTH TCP and UDP
        if is_multihop:
            new_port = "443"
        else:
            new_port = "1194" if new_proto == "udp" else "1443"

        # 1. Find the best template
        template_file = None
        all_files = os.listdir(self.surfshark_dir_path)
        is_multihop = 'mp0' in server_profile

        if is_multihop:
            # For multi-hop, we MUST use another mp0 file as template if possible
            for f in all_files:
                if f.endswith(f'_{proto}.ovpn') and 'mp0' in f and f != server_profile:
                    template_file = f
                    break
            if not template_file:
                for f in all_files:
                    if f.endswith('.ovpn') and 'mp0' in f and f != server_profile:
                        template_file = f
                        break

        if not template_file:
            # Try to find a generic profile with the SAME protocol
            for f in all_files:
                if f.endswith(f'_{proto}.ovpn') and 'st0' not in f and 'mp0' not in f:
                    template_file = f
                    break

        
        # Fallback to any generic profile
        if not template_file:
            for f in all_files:
                if f.endswith('.ovpn') and 'st0' not in f and 'mp0' not in f:
                    template_file = f
                    break
                    
        # Final fallback to absolutely any .ovpn
        if not template_file:
            for f in all_files:
                if f.endswith('.ovpn'):
                    template_file = f
                    break

        if not template_file:
            return False

        try:
            with open(os.path.join(self.surfshark_dir_path, template_file), 'r') as f:
                content = f.read()

            # 2. Update core connection settings
            # Replace remote line with correct hostname and port
            content = re.sub(r'remote .*? \d+', f'remote {new_remote} {new_port}', content)
            # Replace proto line
            content = re.sub(r'proto (udp|tcp)', f'proto {new_proto}', content)

            # 3. Clean up protocol-incompatible options and server-pushed junk
            if new_proto == "tcp":
                content = re.sub(r'^(fast-io|explicit-exit-notify)', r'#\1', content, flags=re.MULTILINE)
            
            # Silence server-pushed warnings
            content += "\npull-filter ignore \"explicit-exit-notify\""
            content += "\npull-filter ignore \"block-outside-dns\""

            # 4. Modernize cipher to avoid warnings in OpenVPN 2.6+
            if 'data-ciphers ' not in content:
                # Add data-ciphers and ensure we're using a modern one
                content = re.sub(r'^cipher .*', 'data-ciphers AES-256-GCM:AES-128-GCM:CHACHA20-POLY1305\ncipher AES-256-GCM', content, flags=re.MULTILINE)

            with open(target_path, 'w') as f:
                f.write(content)
            return True
        except Exception:
            return False

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

        if not self._ensure_profile_exists(server_profile):
            return False

        # Need to run command in new bash and background to avoid locking extension
        # We use --script-security 2 and our custom DNS script to prevent DNS leaks
        cmd = [
            "pkexec", "bash", "-lc",
            f"{self.installed_path} "
            f"--config {self.surfshark_dir_path}/{server_profile} "
            f"--auth-user-pass {self.config_file_path} "
            f"--script-security 2 "
            f"--up {self.dns_script_path} "
            f"--down {self.dns_script_path} "
            f"--down-pre &"
        ]
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
        Also verifies if a tun interface exists.

        Returns:
            The filename of the connected .ovpn profile if active, None otherwise.
        """
        if not self.is_installed():
            return None

        # Check for tun interface existence as a more reliable indicator
        try:
            interfaces = os.listdir('/sys/class/net')
            if not any(iface.startswith('tun') for iface in interfaces):
                return None
        except Exception:
            pass

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
