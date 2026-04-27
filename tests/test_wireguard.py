"""
Unit tests for the WireGuardClient class logic.
Focuses on dynamic configuration generation.
"""

import pytest
from src.wireguard_client import WireGuardClient

def test_generate_config():
    """
    Verifies that the WireGuard configuration string is correctly formatted
    with the provided keys and endpoints.
    """
    client = WireGuardClient("/tmp")
    privkey = "test_privkey"
    pubkey = "test_pubkey"
    endpoint = "test.surfshark.com"
    dns = "1.1.1.1, 8.8.8.8"
    
    config = client.generate_config(privkey, pubkey, endpoint, dns)
    
    assert f"PrivateKey = {privkey}" in config
    assert f"PublicKey = {pubkey}" in config
    assert f"Endpoint = {endpoint}:51820" in config
    assert f"DNS = {dns}" in config
    assert "Address = 10.14.0.2/16" in config
