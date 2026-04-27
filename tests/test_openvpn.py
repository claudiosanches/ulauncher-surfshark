"""
Unit tests for the OpenVPNClient class logic.
Focuses on port selection and configuration modernization.
"""

import pytest
from src.openvpn_client import OpenVPNClient

def test_get_port_for_protocol():
    """
    Verifies that the correct ports are selected for regular and Multi-Hop protocols.
    - Regular: UDP (1194), TCP (1443)
    - Multi-Hop: All (443)
    """
    client = OpenVPNClient("/tmp", "/tmp/config")
    
    # Regular connections
    assert client.get_port_for_protocol("udp", is_multihop=False) == "1194"
    assert client.get_port_for_protocol("tcp", is_multihop=False) == "1443"
    
    # Multi-Hop connections
    assert client.get_port_for_protocol("udp", is_multihop=True) == "443"
    assert client.get_port_for_protocol("tcp", is_multihop=True) == "443"

def test_modernize_config_basic():
    """
    Ensures that a raw configuration is modernized with security and verification directives.
    """
    client = OpenVPNClient("/tmp", "/tmp/config")
    original = "client\nproto udp\nremote test.com 1194\ncipher AES-256-CBC"
    modernized = client.modernize_config(original, "udp", is_multihop=False)
    
    assert "data-ciphers AES-256-GCM" in modernized
    assert "cipher AES-256-GCM" in modernized
    assert "pull-filter ignore" in modernized
    assert "remote-cert-tls server" in modernized

def test_modernize_config_tcp_cleanup():
    """
    Verifies that UDP-only options are correctly disabled when using TCP.
    """
    client = OpenVPNClient("/tmp", "/tmp/config")
    original = "client\nproto tcp\nfast-io\nexplicit-exit-notify"
    modernized = client.modernize_config(original, "tcp", is_multihop=False)
    
    assert "#fast-io" in modernized
    assert "#explicit-exit-notify" in modernized

def test_modernize_config_multihop_port():
    """
    Checks if Multi-Hop port correction (443) is applied during modernization.
    """
    client = OpenVPNClient("/tmp", "/tmp/config")
    original = "client\nproto tcp\nremote test-mp001.com 1443"
    modernized = client.modernize_config(original, "tcp", is_multihop=True, server_profile="test-mp001_tcp.ovpn")
    
    assert "remote test-mp001 443" in modernized
