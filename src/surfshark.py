import os
import json
import re
import time
import subprocess
import requests
import zipfile
import shutil
import io
import tempfile
from typing import List, Dict, Optional, Any
from .utils import Utils
from .openvpn_client import OpenVPNClient
from .wireguard_client import WireGuardClient

class Surf:
    """Core class for managing Surfshark VPN servers and clients."""

    def __init__(self) -> None:
        """Initializes the Surfshark manager, setting up paths and clients."""
        # Hidden data directory for all volatile/sensitive files
        self.data_dir = Utils.get_path(".data")
        os.makedirs(self.data_dir, exist_ok=True)

        self.cache_path = os.path.join(self.data_dir, "cache.json")
        self.aliases_path = Utils.get_path("src/aliases.json")

        self.api_servers: List[Dict[str, Any]] = []
        self.aliases: Dict[str, str] = {}

        # Load aliases
        if os.path.exists(self.aliases_path):
            try:
                with open(self.aliases_path, "r") as f:
                    self.aliases = json.load(f)
            except Exception:
                pass

        # Load cache if available
        if os.path.exists(self.cache_path):
            try:
                with open(self.cache_path, "r") as f:
                    self.api_servers = json.load(f)
            except Exception:
                pass

        self.surfshark_dir_path: str = os.path.join(self.data_dir, "server_profiles")
        self.wireguard_dir_path: str = os.path.join(self.data_dir, "wireguard_profiles")
        self.config_file_path: str = os.path.join(self.data_dir, "service_credentials.conf")

        os.makedirs(self.surfshark_dir_path, exist_ok=True)
        os.makedirs(self.wireguard_dir_path, exist_ok=True)

        self.ovpn_client = OpenVPNClient(self.surfshark_dir_path, self.config_file_path)
        self.wg_client = WireGuardClient(self.wireguard_dir_path)

        # Cache for connection status to avoid frequent API calls
        self._status_cache: Dict[str, Any] = {}
        self._status_cache_time: float = 0
        self._status_cache_ttl: int = 60 # Seconds

        self.reg_servers: List[Dict[str, Any]] = []
        self.st_servers: List[Dict[str, Any]] = []
        self.mp_servers: List[Dict[str, Any]] = []
        self.wg_reg_servers: List[Dict[str, Any]] = []
        self.wg_st_servers: List[Dict[str, Any]] = []
        self.wg_mp_servers: List[Dict[str, Any]] = []
        self.wg_servers: List[Dict[str, Any]] = [] # For backward compatibility

        self.wg_privkey: str = ""

        self.update_server_lists()

    def is_installed(self) -> bool:
        """Checks if any supported VPN client is installed."""
        return self.ovpn_client.is_installed() or self.wg_client.is_installed()

    def get_server_details(self, profile_name: str) -> Optional[Dict[str, Any]]:
        """Extracts server metadata from a profile filename or connection name."""
        if not profile_name:
            return None

        server_code = profile_name.replace('.ovpn', '').replace('.conf', '')

        # Check API servers (cached)
        for s in self.api_servers:
            conn_name = s.get("connectionName", "")
            # Robust matching: hostname in filename or filename starts with hostname
            if conn_name and (conn_name == profile_name or conn_name in profile_name or profile_name.startswith(conn_name)):
                code = conn_name.split(".prod")[0]
                return {
                    "code": code,
                    "country": s.get("country", ""),
                    "countryCode": s.get("countryCode", ""),
                    "city": s.get("location", ""),
                    "type": s.get("endpoint_type", "generic"),
                    "altSearch": self.aliases.get(code, "")
                }

        # Fallback for local profiles not found in API cache
        is_mp = 'mp0' in profile_name or profile_name.startswith('multihop-')
        is_st = 'st0' in profile_name

        return {
            "code": server_code,
            "country": server_code,
            "countryCode": "",
            "city": "",
            "type": "double" if is_mp else ("static" if is_st else "generic"),
            "altSearch": " "
        }

    def flag_name(self, country_code: str) -> str:
        """Generates the flag icon filename from ISO country code."""
        if not country_code:
            return "../icon.svg" # Relative to images/flags/
        return f"{country_code.lower()}.svg"

    def populate_server_object(self, server_details: Dict[str, Any], profile_name: str) -> Optional[Dict[str, Any]]:
        """Creates a enriched server object for Ulauncher results."""
        if not server_details or not profile_name:
            return None

        # Determine connection type label
        stype = server_details.get("type", "generic")
        if not profile_name.endswith('.ovpn'):
            conn_type = "WireGuard"
            if stype == "static": conn_type = "WireGuard (Static)"
            elif stype in ["double", "obfuscated"]: conn_type = "WireGuard (MultiHop)"
        else:
            proto = "TCP" if "tcp.ovpn" in profile_name else "UDP"
            if stype == "static": conn_type = f"OpenVPN (Static {proto})"
            elif stype in ["double", "obfuscated"]: conn_type = f"OpenVPN (MultiHop {proto})"
            else: conn_type = f"OpenVPN ({proto})"

        return {
            "country": server_details["country"],
            "city": server_details["city"],
            "alt_word": server_details.get("altSearch", ""),
            "flag_file": self.flag_name(server_details.get("countryCode", "")),
            "conn_type": conn_type,
            "server_profile": profile_name
        }

    def _fetch_api_servers(self, endpoint_type: str) -> List[Dict[str, Any]]:
        """Helper to fetch servers from specific API endpoints."""
        try:
            url = f"https://api.surfshark.com/v4/server/clusters/{endpoint_type}"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    for server in data:
                        server["endpoint_type"] = endpoint_type
                    return data
        except Exception:
            pass
        return []

    def refresh_server_list(self) -> None:
        """Fetches latest servers from API and updates cache."""
        new_api_servers = []
        for etype in ["generic", "obfuscated", "static"]:
            new_api_servers.extend(self._fetch_api_servers(etype))

        if new_api_servers:
            self.api_servers = new_api_servers
            try:
                with open(self.cache_path, "w") as f:
                    json.dump(self.api_servers, f, indent=4)
            except Exception:
                pass

        self.update_server_lists()

    def update_server_lists(self) -> None:
        """Updates the in-memory server lists based on cached API data."""
        self.wg_reg_servers = []
        self.wg_st_servers = []
        self.wg_mp_servers = []
        self.wg_servers = []
        self.reg_servers = []
        self.st_servers = []
        self.mp_servers = []

        for s in self.api_servers:
            conn_name = s.get("connectionName")
            if not conn_name:
                continue

            code = conn_name.split(".prod")[0]
            etype = s.get("endpoint_type", "generic")
            details = {
                "country": s.get("country", ""),
                "countryCode": s.get("countryCode", ""),
                "city": s.get("location", ""),
                "type": etype,
                "altSearch": self.aliases.get(code, "")
            }

            # WireGuard entries (if pubKey exists)
            if s.get("pubKey"):
                wg_obj = self.populate_server_object(details, conn_name)
                if wg_obj:
                    self.wg_servers.append(wg_obj)
                    if etype == "static": self.wg_st_servers.append(wg_obj)
                    elif etype == "obfuscated": self.wg_mp_servers.append(wg_obj)
                    else: self.wg_reg_servers.append(wg_obj)

            # OpenVPN entries (TCP and UDP)
            for proto in ["udp", "tcp"]:
                p_name = f"{conn_name}_{proto}.ovpn"
                ovpn_obj = self.populate_server_object(details, p_name)
                if ovpn_obj:
                    if etype == "static": self.st_servers.append(ovpn_obj)
                    elif etype == "obfuscated": self.mp_servers.append(ovpn_obj)
                    else: self.reg_servers.append(ovpn_obj)

    def connect(self, server: str, wg_privkey: Optional[str] = None, wg_dns: Optional[str] = None) -> None:
        """Orchestrates the connection to a VPN server."""
        server_details = self.get_server_details(server)
        is_ovpn = server.endswith('.ovpn')
        proto_name = "OpenVPN" if is_ovpn else "WireGuard"

        Utils.notify(
            f'Connecting to {server_details["country"]} - {server_details["city"]}...',
            f"Establishing {proto_name} connection to Surfshark.",
        )

        success = False
        if is_ovpn:
            success = self.ovpn_client.connect(server)
        else:
            # WireGuard connection
            target_server = next((s for s in self.api_servers if s.get("connectionName") == server), None)
            success = self.wg_client.connect(server, target_server=target_server, wg_privkey=wg_privkey, wg_dns=wg_dns)

        if success:
            # Wait for interface to initialize
            time.sleep(3 if is_ovpn else 1.5)
            status = self.get_status()
            if status:
                secured_info = " (Secured)" if status.get("secured") else ""
                Utils.notify(
                    f'Connected to {server_details["country"]} - {server_details["city"]}{secured_info}',
                    f"Your {proto_name} tunnel is now active.",
                )
                return

        error_hint = "Check your credentials and OpenVPN logs." if is_ovpn else "Check your WireGuard Private Key and tools."
        Utils.notify(
            f'Connection failed.',
            f"Could not establish {proto_name} connection to {server_details['city']}. {error_hint}"
        )

    def disconnect(self) -> None:
        """Disconnects from any active Surfshark VPN session."""
        Utils.notify("Disconnecting...", "Tearing down VPN connection.")
        self.ovpn_client.disconnect()
        self.wg_client.disconnect()
        time.sleep(2)
        if not self.get_status():
            Utils.notify("Disconnected.", "You are no longer connected to Surfshark.")
        else:
            Utils.notify("Disconnection Error.", "The VPN tunnel might still be active. Check system logs.")

    def get_status(self) -> Optional[Dict[str, Any]]:
        """
        Retrieves the current VPN connection status.
        
        Checks both OpenVPN and WireGuard clients for an active connection
        and returns enriched metadata if found.

        Returns:
            A dictionary containing server details and security status, or None.
        """
        # Check OpenVPN first, then WireGuard
        connection = self.ovpn_client.get_status() or self.wg_client.get_status()
        
        if connection:
            return self._enrich_status(connection)
            
        return None

    def _enrich_status(self, profile_name: str) -> Optional[Dict[str, Any]]:
        """
        Enriches a raw profile name with metadata and real-time security status.

        Args:
            profile_name: The filename or connection identifier of the active tunnel.

        Returns:
            A dictionary with country, city, IP, and security status.
        """
        status = self.populate_server_object(self.get_server_details(profile_name), profile_name)
        if status:
            sec_info = self.is_secured()
            status["secured"] = sec_info["secured"]
            status["ip"] = sec_info["ip"]
        return status

    def is_secured(self) -> Dict[str, Any]:
        """Verifies if the current connection is secured and returns IP info with caching."""
        now = time.time()
        if self._status_cache and (now - self._status_cache_time) < self._status_cache_ttl:
            return self._status_cache

        result = {"secured": False, "ip": "Unknown"}
        try:
            # We use a short timeout to avoid blocking the UI
            response = requests.get("https://api.surfshark.com/v1/server/user", timeout=1.5)
            if response.status_code == 200:
                data = response.json()
                result["secured"] = data.get("secured", False)
                result["ip"] = data.get("ip", "Unknown")
        except Exception:
            pass

        self._status_cache = result
        self._status_cache_time = now
        return result

    def refresh_openvpn_connections(self) -> None:
        """Downloads and refreshes OpenVPN connection profiles and API cache."""
        Utils.notify("Refreshing...", "Updating server profiles and API cache.")
        try:
            self.refresh_server_list()

            # 1. Download Regular Configurations
            url = "https://my.surfshark.com/vpn/api/v1/server/configurations"
            response = requests.get(url, timeout=30)
            if response.status_code != 200:
                raise Exception(f"HTTP Error {response.status_code}")

            # Extract to temporary directory
            with tempfile.TemporaryDirectory() as tmp_dir:
                with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                    z.extractall(tmp_dir)

                # Check if we got some .ovpn files
                new_profiles = [f for f in os.listdir(tmp_dir) if f.endswith('.ovpn')]

                if not new_profiles:
                    raise Exception("Downloaded archive is empty or invalid.")

                # Non-destructive swap:
                # 1. Clean current profiles directory
                if os.path.exists(self.surfshark_dir_path):
                    for f in os.listdir(self.surfshark_dir_path):
                        if f != "update-dns.sh":
                            os.remove(os.path.join(self.surfshark_dir_path, f))
                else:
                    os.makedirs(self.surfshark_dir_path, exist_ok=True)

                # 2. Move new profiles to the final destination
                for f in new_profiles:
                    shutil.move(os.path.join(tmp_dir, f), os.path.join(self.surfshark_dir_path, f))

            self.update_server_lists()
            Utils.notify("Refreshed.", "Surfshark database successfully updated.")
        except Exception as e:
            Utils.notify("Update Failed.", f"Error refreshing database: {str(e)}")
    def is_credential_file_exists(self) -> bool:
        return os.path.exists(self.config_file_path)

    def update_credential_file(self, uname: Optional[str], passwd: Optional[str]) -> None:
        if not self.is_credential_file_exists():
            with open(self.config_file_path, 'w') as f: f.write("\n\n")
            os.chmod(self.config_file_path, 0o600)
        if uname or passwd:
            with open(self.config_file_path, 'r') as f: lines = f.readlines()
            while len(lines) < 2: lines.append("\n")
            if uname: lines[0] = uname.strip() + "\n"
            if passwd: lines[1] = passwd.strip() + "\n"
            with open(self.config_file_path, 'w') as f: f.writelines(lines)
