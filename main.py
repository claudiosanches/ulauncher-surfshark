from ulauncher.api.client.Extension import Extension
from ulauncher.api.shared.event import (
    KeywordQueryEvent,
    ItemEnterEvent,
    PreferencesEvent,
    PreferencesUpdateEvent,
)
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction
from src.surfshark import Surf
from src.utils import Utils
from src.listeners import (
    KeywordQueryEventListener,
    ItemEnterEventListener,
    PreferencesEventListener,
    PreferencesUpdateEventListener,
)

class SurfExtension(Extension):
    """Main extension class for Surfshark Ulauncher integration."""

    keyword = None
    max_server_entries = None
    uname = None
    passwd = None
    wg_privkey = None
    wg_dns = None

    def __init__(self):
        """Initializes the extension and subscribes to events."""
        super(SurfExtension, self).__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        self.subscribe(ItemEnterEvent, ItemEnterEventListener())
        self.subscribe(PreferencesEvent, PreferencesEventListener())
        self.subscribe(PreferencesUpdateEvent, PreferencesUpdateEventListener())
        self.surf = Surf()

    def update_credentials(self):
        """Ensures service credentials file is present and up-to-date."""
        if not self.surf.is_credential_file_exists():
            self.update_username(self.uname)
            self.update_password(self.passwd)
        self.surf.wg_privkey = self.wg_privkey

    def update_username(self, uname):
        """Updates the service username in the configuration file."""
        self.surf.update_credential_file(uname, None)

    def update_password(self, passwd):
        """Updates the service password in the configuration file."""
        self.surf.update_credential_file(None, passwd)

    def filter_server_list(self, query, server_type, server_list):
        """
        Filters a list of servers based on a search query and connection type.

        Args:
            query: The search string.
            server_type: The connection type (udp, tcp, etc.) to filter by.
            server_list: The list of server objects to filter.

        Returns:
            A filtered list of server objects.
        """
        self.update_credentials()
        query = query.lower() if query else ""
        if query:
            return [s for s in server_list if ((s["country"].lower().startswith(query)
                                                    or s["alt_word"].lower().startswith(query)
                                                    or s["city"].lower().startswith(query))
                                     and server_type in s["conn_type"].lower())]
        else:
            return [s for s in server_list if server_type in s["conn_type"].lower()]

    def get_server_result_items(self, query, server_type):
        """
        Generates Ulauncher result items for VPN servers.

        Args:
            query: The search query for server names.
            server_type: The connection type key (wg, mp_udp, etc.).

        Returns:
            A list of ExtensionResultItem objects.
        """
        server_type = server_type.lower() if server_type else "udp"
        items = []
        data = []

        if server_type == 'wg':
            data = self.filter_server_list(query, '', self.surf.wg_reg_servers)
        elif server_type == 'wg_st':
            data = self.filter_server_list(query, '', self.surf.wg_st_servers)
        elif server_type == 'wg_mp':
            data = self.filter_server_list(query, '', self.surf.wg_mp_servers)
            if not data:
                return [
                    ExtensionResultItem(
                        icon=Utils.get_path("images/icon.svg"),
                        name="WireGuard MultiHop unavailable",
                        description="Surfshark is not exposing server public keys for MultiHop locations.",
                        highlightable=False,
                    )
                ]
        elif server_type.startswith('mp'):
            server_type = server_type.replace('mp_', '')
            data = self.filter_server_list(query, server_type, self.surf.mp_servers)
        elif server_type.startswith('st'):
            server_type = server_type.replace('st_', '')
            data = self.filter_server_list(query, server_type, self.surf.st_servers)
        else:
            data = self.filter_server_list(query, server_type, self.surf.reg_servers)

        for server in data[0:self.max_server_entries]:
            items.append(
                ExtensionResultItem(
                    icon=Utils.get_path(f'images/flags/{server["flag_file"]}'),
                    name=server["country"] + " - " + server["city"],
                    highlightable=False,
                    on_enter=ExtensionCustomAction(
                        {
                            "action": "CONNECT_TO_SERVER",
                            "server": server["server_profile"],
                        }
                    ),
                )
            )
        return items

    def get_connection_status(self):
        """Retrieves the current VPN connection status."""
        return self.surf.get_status()

if __name__ == "__main__":
    SurfExtension().run()
