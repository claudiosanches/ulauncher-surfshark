import pathlib
from typing import List, Dict
from gi.repository import Notify

class Utils:
    """Utility class providing helper methods for the Surfshark extension."""

    @staticmethod
    def get_path(filename: str) -> str:
        """
        Returns the absolute path to a file relative to the extension root.

        Args:
            filename: The name or relative path of the file.

        Returns:
            The absolute path to the file.
        """
        # __file__ is in src/utils.py, so parent is src/, and parent.parent is the root
        current_dir = pathlib.Path(__file__).parent.parent.absolute()
        return str(current_dir / filename)

    @staticmethod
    def notify(title: str, message: str) -> None:
        """
        Displays a system GUI notification.

        Args:
            title: The title of the notification.
            message: The message body of the notification.
        """
        Notify.init("Surfshark")
        notification = Notify.Notification.new(
            title,
            message,
            Utils.get_path("images/icon.svg"),
        )
        notification.set_timeout(1000)
        notification.show()

    @staticmethod
    def get_available_connection_types() -> List[Dict[str, str]]:
        """
        Returns a list of available VPN connection types and their metadata.

        Returns:
            A list of dictionaries containing connection type details (name, description, action).
        """
        available_conn_types = [
            {
                "name": "WireGuard",
                "description": "Connect to VPN using WireGuard",
                "action": "wg"
            },
            {
                "name": "UDP",
                "description": "Connect to VPN using UDP",
                "action": "udp"
            },
            {
                "name": "TCP",
                "description": "Connect to VPN using TCP",
                "action": "tcp"
            },
            {
                "name": "Static WireGuard",
                "description": "Connect to VPN with Static IP - WireGuard",
                "action": "wg_st"
            },
            {
                "name": "Static UDP",
                "description": "Connect to VPN with Static IP - UDP",
                "action": "st_udp"
            },
            {
                "name": "Static TCP",
                "description": "Connect to VPN with Static IP - TCP",
                "action": "st_tcp"
            },
            {
                "name": "MultiHop UDP",
                "description": "Connect to VPN with MultiHop UDP",
                "action": "mp_udp"
            },
            {
                "name": "MultiHop TCP",
                "description": "Connect to VPN with MultiHop TCP",
                "action": "mp_tcp"
            }
        ]
        return available_conn_types
