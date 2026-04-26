# Ulauncher Surfshark

Simple [Ulauncher](https://ulauncher.io) extension to quickly toggle and connect to Surfshark VPN servers using **OpenVPN** or **WireGuard**.

![screenshot](images/screenshot.png)

*Recommendation: If you like the icons in the screenshot, I'm using the [Tela-circle-icon-theme](https://github.com/vinceliuice/Tela-circle-icon-theme) on my machine!*

## Features

- **WireGuard Support**: Fully automated WireGuard integration. Just paste your Private Key and connect.
- **OpenVPN Support**: Support for traditional `.ovpn` profiles.
- **Auto-Discovery**: Fetches the latest server list (Standard, Multi-Hop, Static IP) directly from Surfshark's API.
- **Smart Search**: Supports searching by country, city, and common aliases (e.g., "UK", "UAE", "HK").
- **Fast Initialization**: Uses a local cache for near-instant loading.
- **Beautiful UI**: Modern, high-quality rounded flag icons for all locations.

> **Disclaimer**: This is an unofficial extension and is not affiliated with, maintained, or endorsed by Surfshark. Use it at your own risk.

## Installation

### Dependencies

This extension requires the following components to function correctly:

- **OpenVPN**: `sudo apt install openvpn` (for OpenVPN connections)
- **WireGuard**: `sudo apt install wireguard-tools` (for WireGuard connections)
- **wget** and **unzip**: (for profile discovery)

> **Note:** It is highly recommended to **restart Ulauncher** after installing the dependencies or the extension itself to ensure all components are correctly detected.

### Via Ulauncher Interface

1. Open Ulauncher Settings -> Extensions -> Add extension.
2. Paste the following URL:
   `https://github.com/claudiosanches/ulauncher-surfshark`
3. Click **Add**.

### Manual Installation (Developer Version)

1. Open a terminal.
2. Create the Ulauncher extensions directory if it doesn't exist:
   ```bash
   mkdir -p ~/.local/share/ulauncher/extensions
   ```
3. Clone this repository into the extensions folder:
   ```bash
   git clone https://github.com/claudiosanches/ulauncher-surfshark ~/.local/share/ulauncher/extensions/com.github.claudiosanches.ulauncher-surfshark
   ```
4. Restart Ulauncher.

## Settings

In Ulauncher GUI, you can set the following preferences:

- **Trigger keyword**: Keyword to trigger the extension (defaults to `surf`).
- **Maximum number of servers**: Limit the number of servers shown in the list.
- **Surfshark service username**: Your manual setup username (not your email).
- **Surfshark service password**: Your manual setup password.
- **Surfshark WireGuard Private Key**: Your generated WireGuard private key.

## Usage

Open Ulauncher and type the set up keyword (defaults to `surf`).

- **`surf connect`**: Browse the list of available servers.
  - You can filter by name, city, or connection type.
- **`surf disconnect`**: Disconnect from the active VPN session.
- **`surf refresh`**: Manually update the server database and download OpenVPN profiles.

## Credits

- **Flag Icons**: This project uses the beautiful rounded flags from the [circle-flags](https://github.com/HatScripts/circle-flags) project by [HatScripts](https://github.com/HatScripts).
- **Inspiration**: This project is a significantly refactored and modernized version of the original [ulauncher-surfshark](https://github.com/saini-anshul/ulauncher-surfshark) extension by [Anshul Saini](https://github.com/saini-anshul). It has been updated for Python 3, WireGuard support, and modern Surfshark APIs.

## License

This project is licensed under the terms of the GPLv3 license. See the [LICENSE](LICENSE) file for details.
