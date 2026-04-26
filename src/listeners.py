from typing import Any
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import (
    KeywordQueryEvent,
    ItemEnterEvent,
    PreferencesEvent,
    PreferencesUpdateEvent,
)
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction
from ulauncher.api.shared.action.SetUserQueryAction import SetUserQueryAction
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction
from .utils import Utils

class KeywordQueryEventListener(EventListener):
    """Listens for and handles keyword query events from Ulauncher."""

    def on_event(self, event: KeywordQueryEvent, extension) -> RenderResultListAction:
        """
        Handles the keyword query event.

        Args:
            event: The query event containing the user's input.
            extension: The extension instance.

        Returns:
            A RenderResultListAction with the items to display in Ulauncher.
        """
        items = []

        if not extension.surf.is_installed():
            items.append(
                ExtensionResultItem(
                    icon=Utils.get_path("images/icon.svg"),
                    name="Extension failed to load :/",
                    description="Make sure to have openvpn or wireguard-tools, wget, and unzip installed on system.",
                    highlightable=False,
                    on_enter=HideWindowAction(),
                )
            )
            return RenderResultListAction(items)

        argument = event.get_argument() or ""
        command, connection_type, server_query = (argument.split(" ", 2) + [None] + [None])[:3]

        if not command:
            server_connected = extension.get_connection_status()
            if server_connected:
                items.extend(
                    [
                        ExtensionResultItem(
                            icon=Utils.get_path(f'images/flags/{server_connected["flag_file"]}'),
                            name="Connected",
                            description=(server_connected["country"] + " - " + server_connected["city"] + ": " + server_connected["conn_type"]),
                            highlightable=False,
                            on_enter=SetUserQueryAction(
                                f'{extension.keyword or " "} '
                            ),
                        ),
                    ]
                )
            else:
                items.extend(
                    [
                        ExtensionResultItem(
                            icon=Utils.get_path("images/icon.svg"),
                            name="Connect",
                            description="Connect to Surfshark: choose from a list of servers",
                            highlightable=False,
                            on_enter=SetUserQueryAction(
                                f'{extension.keyword or " "} connect '
                            ),
                        ),
                    ]
                )

            items.extend(
                [
                    ExtensionResultItem(
                        icon=Utils.get_path("images/icon.svg"),
                        name="Disconnect",
                        description="Disconnect from Surfshark VPN",
                        highlightable=False,
                        on_enter=ExtensionCustomAction({"action": "DISCONNECT"}),
                    ),
                    ExtensionResultItem(
                        icon=Utils.get_path("images/icon.svg"),
                        name="Refresh DB",
                        description="Refresh Surfshark VPN connection database",
                        highlightable=False,
                        on_enter=ExtensionCustomAction({"action": "REFRESHDB"}),
                    ),
                ]
            )

        elif command in "connect":
            if not connection_type:
                for conn_type in Utils.get_available_connection_types():
                    items.append(
                        ExtensionResultItem(
                            icon=Utils.get_path("images/icon.svg"),
                            name=conn_type["name"],
                            description=conn_type["description"],
                            highlightable=False,
                            on_enter=SetUserQueryAction(
                                f'{extension.keyword or " "} connect {conn_type["action"]} '
                            ),
                        )
                    )
            else:
                server_list = extension.get_server_result_items(server_query, connection_type)
                if server_list:
                    items.extend(server_list)
                else:
                    items.extend(
                        [
                            ExtensionResultItem(
                                icon=Utils.get_path("images/icon.svg"),
                                name="No servers found",
                                description="Try a different search or refresh the database",
                                highlightable=False,
                                on_enter=SetUserQueryAction(
                                    f'{extension.keyword or " "} '
                                ),
                            ),
                        ]
                    )
        else:
            items.extend(
                [
                    ExtensionResultItem(
                        icon=Utils.get_path("images/icon.svg"),
                        name="Invalid selection.",
                        description=(f"Try again."),
                        highlightable=False,
                        on_enter=SetUserQueryAction(
                            f'{extension.keyword or " "} '
                        ),
                    ),
                ]
            )

        return RenderResultListAction(items)


class ItemEnterEventListener(EventListener):
    """Listens for and handles item enter events (actions) from Ulauncher."""

    def on_event(self, event: ItemEnterEvent, extension) -> Any:
        """
        Handles the item enter event.

        Args:
            event: The event containing the action data.
            extension: The extension instance.
        """
        data = event.get_data()
        action = data["action"]

        if action == "CONNECT":
            return RenderResultListAction(extension.get_server_result_items())

        if action == "DISCONNECT":
            return extension.surf.disconnect()

        if action == "REFRESHDB":
            return extension.surf.refresh_openvpn_connections()

        if action == "CONNECT_TO_SERVER":
            return extension.surf.connect(data["server"], extension.wg_privkey, extension.wg_dns)


class PreferencesEventListener(EventListener):
    """Listens for and handles initial preferences loading."""

    def on_event(self, event: PreferencesEvent, extension) -> None:
        """
        Handles the preferences event.

        Args:
            event: The event containing initial preferences.
            extension: The extension instance.
        """
        extension.keyword = event.preferences["surf_kw"]
        extension.uname = event.preferences["surf_uname"]
        extension.passwd = event.preferences["surf_passwd"]
        extension.wg_privkey = event.preferences.get("surf_wg_privkey", "")
        extension.wg_dns = event.preferences.get("surf_wg_dns", "162.252.172.57, 149.154.159.92")
        try:
            extension.max_server_entries = int(event.preferences["surf_max_entry"])
        except ValueError:
            extension.max_server_entries = 10


class PreferencesUpdateEventListener(EventListener):
    """Listens for and handles real-time preference updates."""

    def on_event(self, event: PreferencesUpdateEvent, extension) -> None:
        """
        Handles the preferences update event.

        Args:
            event: The event containing the updated preference.
            extension: The extension instance.
        """
        if event.id == "surf_kw":
            extension.keyword = event.new_value
        if event.id == "surf_uname":
            extension.update_username(event.new_value)
        if event.id == "surf_passwd":
            extension.update_password(event.new_value)
        if event.id == "surf_wg_privkey":
            extension.wg_privkey = event.new_value
        if event.id == "surf_wg_dns":
            extension.wg_dns = event.new_value
        if event.id == "surf_max_entry":
            try:
                extension.max_server_entries = int(event.new_value)
            except ValueError:
                extension.max_server_entries = 10
