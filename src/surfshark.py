import os
import json
import re
import time
import subprocess
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
        
        self.reg_servers: List[Dict[str, Any]] = []
        self.st_servers: List[Dict[str, Any]] = []
        self.mp_servers: List[Dict[str, Any]] = []
        self.wg_servers: List[Dict[str, Any]] = []
        
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
            if conn_name == profile_name or conn_name == f"{server_code}.prod.surfshark.com" or conn_name in profile_name:
                code = conn_name.split(".prod")[0]
                return {
                    "code": code,
                    "country": s.get("country", ""),
                    "countryCode": s.get("countryCode", ""),
                    "city": s.get("location", ""),
                    "altSearch": self.aliases.get(code, "")
                }

        return {
            "code": server_code,
            "country": server_code,
            "countryCode": "",
            "city": "",
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
        
        return {
            "country": server_details["country"],
            "city": server_details["city"],
            "alt_word": server_details.get("altSearch", ""),
            "flag_file": self.flag_name(server_details.get("countryCode", "")),
            "conn_type": self.get_conn_type_from_profile_name(profile_name),
            "server_profile": profile_name
        }

    def _fetch_api_servers(self, endpoint_type: str) -> List[Dict[str, Any]]:
        """Helper to fetch servers from specific API endpoints."""
        try:
            url = f"https://api.surfshark.com/v4/server/clusters/{endpoint_type}"
            res = subprocess.run(["curl", "-s", url], capture_output=True, text=True)
            if res.returncode == 0:
                data = json.loads(res.stdout)
                if isinstance(data, list):
                    return data
        except Exception:
            pass
        return []

    def refresh_server_list(self) -> None:
        """Fetches latest servers from API and updates cache."""
        new_api_servers = []
        for etype in ["generic", "double", "static"]:
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
        """Updates the in-memory server lists based on cached API data and local profiles."""
        # Map API servers to wg_servers
        self.wg_servers = []
        for s in self.api_servers:
            if s.get("pubKey") and s.get("connectionName"):
                conn_name = s["connectionName"]
                code = conn_name.split(".prod")[0]
                self.wg_servers.append({
                    "country": s["country"],
                    "city": s["location"],
                    "alt_word": self.aliases.get(code, ""),
                    "flag_file": self.flag_name(s.get("countryCode", "")),
                    "conn_type": "WireGuard",
                    "server_profile": conn_name,
                    "pubKey": s["pubKey"]
                })

        # OpenVPN local profiles
        if os.path.exists(self.surfshark_dir_path):
            all_ovpn = [f for f in os.listdir(self.surfshark_dir_path) if f.endswith('.ovpn')]
            self.reg_servers = []
            self.st_servers = []
            self.mp_servers = []
            
            for p in all_ovpn:
                obj = self.populate_server_object(self.get_server_details(p), p)
                if obj:
                    if 'st0' in p:
                        self.st_servers.append(obj)
                    elif 'mp0' in p or p.startswith('multihop-'):
                        self.mp_servers.append(obj)
                    else:
                        self.reg_servers.append(obj)

    def connect(self, server: str, wg_privkey: Optional[str] = None, wg_dns: Optional[str] = None) -> None:
        """Orchestrates the connection to a VPN server."""
        server_details = self.get_server_details(server)
        Utils.notify(
            f'Connecting to {server_details["country"]} - {server_details["city"]}...',
            "Connecting you to Surfshark.",
        )
        
        success = False
        if server.endswith('.ovpn'):
            success = self.ovpn_client.connect(server)
        else:
            # WireGuard connection
            target_server = next((s for s in self.api_servers if s.get("connectionName") == server), None)
            success = self.wg_client.connect(server, target_server=target_server, wg_privkey=wg_privkey, wg_dns=wg_dns)

        if success:
            time.sleep(2)
            if self.get_status():
                Utils.notify(
                    f'Connected to {server_details["country"]} - {server_details["city"]}.',
                    "Connected to Surfshark VPN.",
                )
                return
        
        Utils.notify(
            f'Error connecting to {server_details["country"]} - {server_details["city"]}.',
            "Make sure you have the correct dependencies and WireGuard Private Key set."
        )

    def disconnect(self) -> None:
        """Disconnects from any active Surfshark VPN session."""
        Utils.notify("Disconnecting...", "Disconnecting you from Surfshark.")
        self.ovpn_client.disconnect()
        self.wg_client.disconnect()
        time.sleep(2)
        if not self.get_status():
            Utils.notify("Disconnected.", "Disconnected from Surfshark VPN.")
        else:
            Utils.notify("Error while disconnecting.", "There was an error while disconnecting.")

    def get_conn_type_from_profile_name(self, profile_name: str) -> Optional[str]:
        """Returns a user-friendly connection type string."""
        if not profile_name: return None
        if not profile_name.endswith('.ovpn'): return "WireGuard"
        if 'mp0' in profile_name or profile_name.startswith('multihop-'): return "Multi-Point"
        if 'st0' in profile_name: return "Static-IP"
        return "TCP" if 'tcp.ovpn' in profile_name else "UDP"
    
    def get_status(self) -> Optional[Dict[str, Any]]:
        """Returns enriched server details for the active VPN connection, if any."""
        profile_name = self.ovpn_client.get_status()
        if profile_name:
            return self.populate_server_object(self.get_server_details(profile_name), profile_name)
        
        connection_name = self.wg_client.get_status()
        if connection_name:
            return self.populate_server_object(self.get_server_details(connection_name), connection_name)
            
        return None
    
    def refresh_openvpn_connections(self) -> None:
        """Downloads and refreshes OpenVPN connection profiles and API cache."""
        Utils.notify("Refreshing...", "Refreshing connection profiles and API cache.")
        try:
            self.refresh_server_list()
            # Clean old profiles
            if os.path.exists(self.surfshark_dir_path):
                subprocess.run(f"rm {self.surfshark_dir_path}/*.ovpn", shell=True)
            else:
                os.makedirs(self.surfshark_dir_path, exist_ok=True)

            subprocess.run(["wget", "https://my.surfshark.com/vpn/api/v1/server/configurations", "-P", self.surfshark_dir_path], check=True)
            subprocess.run(["unzip", "-o", os.path.join(self.surfshark_dir_path, "configurations"), "-d", self.surfshark_dir_path], check=True)
            self.update_server_lists()
            Utils.notify("Refreshed.", "Profiles and cache refreshed.")
        except Exception as e:
            Utils.notify("Refresh failed.", str(e))

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
