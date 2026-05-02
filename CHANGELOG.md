# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-05-01

### Added

- **WireGuard Support**: Fully automated integration with dynamic configuration generation.
- **MultiHop Support**: Support for Surfshark's MultiHop (Double VPN) servers via OpenVPN.
- **WireGuard MultiHop Detection**: Prepared the WireGuard MultiHop connection type, but Surfshark currently does not expose the required server public keys for MultiHop WireGuard locations.
- **Static IP Support**: Support for Static IP servers via both WireGuard and OpenVPN.
- **Anti-DNS Leak Technology**: Integrated custom DNS management supporting `systemd-resolved` and `resolvconf`.
- **Real-time Verification**: Real-time public IP and security status verification displayed directly in the UI.
- **Robust Metadata Parsing**: Uses Surfshark's API as the primary source of truth for location and server type.
- **Modernized OpenVPN Configs**: Automatic on-the-fly modernization of profiles to use GCM ciphers and pull-filters.
- **Non-Destructive Refresh**: Safe database refresh logic that prevents data loss on failed downloads.
- **Improved UI**: Modernized interface with high-quality rounded flag icons and professional connection labels.
