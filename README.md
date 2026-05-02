# Ulauncher Surfshark

[![CI](https://github.com/claudiosanches/ulauncher-surfshark/actions/workflows/ci.yml/badge.svg)](https://github.com/claudiosanches/ulauncher-surfshark/actions/workflows/ci.yml)

Simple [Ulauncher](https://ulauncher.io) extension to quickly toggle and connect to Surfshark VPN servers using **OpenVPN** or **WireGuard**.

![screenshot](images/screenshot.gif)

*Recommendation: If you like the icons in the screenshot, I'm using the [Tela-circle-icon-theme](https://github.com/vinceliuice/Tela-circle-icon-theme) on my machine!*

## Features

- **WireGuard Support**: Fully automated WireGuard integration. Just paste your Private Key and connect.
- **OpenVPN Support**: Support for traditional `.ovpn` profiles with automatic on-demand generation for Static IP and MultiHop servers.
- **MultiHop Support**: Complete support for Surfshark's MultiHop (Double VPN) servers via OpenVPN.
- **WireGuard MultiHop Detection**: The `wg_mp` connection type is available, but Surfshark currently does not expose server public keys for MultiHop WireGuard locations through the API used by this extension.
- **Anti-DNS Leak Technology**: Integrated custom DNS management (supporting `systemd-resolved` and `resolvconf`) to prevent DNS leaks on OpenVPN connections.
- **Auto-Discovery**: Fetches the latest server list directly from Surfshark's API.
- **Smart Search**: Supports searching by country, city, and common aliases (e.g., "UK", "UAE", "HK").
- **Verified Connection**: Real-time public IP and security status verification displayed directly in the UI.
- **Beautiful UI**: Modern, high-quality rounded flag icons for all locations.

> **Disclaimer**: This is an unofficial extension and is not affiliated with, maintained, or endorsed by Surfshark. Use it at your own risk.

## TODO

- [ ] **WireGuard MultiHop**: The extension is ready to list and connect to WireGuard MultiHop servers if Surfshark starts exposing server public keys for MultiHop locations. Today, those API entries do not include the required server `pubKey`, so OpenVPN remains the supported MultiHop protocol.

## Installation

### Dependencies

This extension requires the following components to function correctly:

- **OpenVPN**: `sudo apt install openvpn` (for OpenVPN connections)
- **WireGuard**: `sudo apt install wireguard-tools` (for WireGuard connections)

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

- **Keyword**: Keyword to trigger the extension (defaults to `surf`).
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
- **Inspiration**: This project is a significantly refactored and modernized version of the original [ulauncher-surfshark](https://github.com/saini-anshul/ulauncher-surfshark) extension by [Anshul Saini](https://github.com/saini-anshul). 
  - *Key improvements in this version include:*
    - Added **WireGuard** support.
    - Added **MultiHop** and **Static IP** support for OpenVPN.
    - Fixed critical **DNS leak issues** via custom DNS management.
    - Replaced external shell dependencies (`wget`, `unzip`, `curl`) with native Python implementations.
    - Added real-time **connection verification** (Secured/Not Secured status with IP).
    - Updated for Python 3 and modern Surfshark APIs.

## License

This project is licensed under the terms of the GPLv3 license. See the [LICENSE](LICENSE) file for details.
