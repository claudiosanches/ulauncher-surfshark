from abc import ABC, abstractmethod
from typing import Optional

class VPNClient(ABC):
    """Abstract base class for VPN client implementations."""

    @abstractmethod
    def connect(self, server_profile: str) -> bool:
        """
        Connects to a VPN server using the specified profile.

        Args:
            server_profile: The filename of the server configuration profile.

        Returns:
            True if the connection process was initiated successfully, False otherwise.
        """
        pass

    @abstractmethod
    def disconnect(self) -> bool:
        """
        Disconnects from the currently active VPN session.

        Returns:
            True if the disconnection process was successful, False otherwise.
        """
        pass

    @abstractmethod
    def get_status(self) -> Optional[str]:
        """
        Retrieves the status of the VPN connection.

        Returns:
            The name of the connected server profile if connected, None otherwise.
        """
        pass

    @abstractmethod
    def is_installed(self) -> bool:
        """
        Checks if the required VPN binary is installed on the system.

        Returns:
            True if installed, False otherwise.
        """
        pass
