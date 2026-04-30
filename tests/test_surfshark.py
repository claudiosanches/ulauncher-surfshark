"""
Unit tests for the Surf class logic.
Focuses on server metadata parsing and flag icon mapping.
"""

import pytest
from unittest.mock import patch, MagicMock
from src.surfshark import Surf

@pytest.fixture
def surf_client():
    """Provides a mocked Surf client for testing."""
    with patch('os.makedirs'), \
         patch('src.surfshark.OpenVPNClient'), \
         patch('src.surfshark.WireGuardClient'), \
         patch('src.surfshark.Utils.get_path', return_value='/tmp'), \
         patch('builtins.open', create=True):
        client = Surf()
        client.api_servers = [
            {
                "country": "Germany",
                "countryCode": "DE",
                "location": "Frankfurt am Main",
                "connectionName": "de-fra-st001.prod.surfshark.com",
                "endpoint_type": "static"
            }
        ]
        return client

def test_get_server_details_from_cache(surf_client):
    """
    Verifies that server metadata is correctly retrieved from the API cache.
    """
    details = surf_client.get_server_details("de-fra-st001.prod.surfshark.com_udp.ovpn")
    assert details["country"] == "Germany"
    assert details["city"] == "Frankfurt am Main"
    assert details["type"] == "static"

def test_get_server_details_fallback(surf_client):
    """
    Ensures that the metadata parser correctly falls back to filename-based detection
    when the server is not in the API cache.
    """
    # Multi-hop fallback
    details = surf_client.get_server_details("multihop-us-nyc.ovpn")
    assert details["type"] == "double"
    
    # Static fallback
    details = surf_client.get_server_details("us-nyc-st001.ovpn")
    assert details["type"] == "static"

def test_flag_name(surf_client):
    """
    Verifies the flag icon filename generation from country codes.
    """
    assert surf_client.flag_name("US") == "us.svg"
    assert surf_client.flag_name("br") == "br.svg"
    assert surf_client.flag_name("") == "../icon.svg"

def test_update_server_lists_adds_wireguard_multihop_with_pubkey(surf_client):
    """
    Verifies that MultiHop servers with WireGuard metadata are exposed
    through the WireGuard MultiHop list.
    """
    surf_client.api_servers = [
        {
            "country": "Canada",
            "countryCode": "CA",
            "location": "Toronto",
            "connectionName": "ca-tor-mp001.prod.surfshark.com",
            "endpoint_type": "obfuscated",
            "pubKey": "test_pubkey"
        }
    ]

    surf_client.update_server_lists()

    assert len(surf_client.wg_mp_servers) == 1
    assert surf_client.wg_mp_servers[0]["conn_type"] == "WireGuard (MultiHop)"
    assert surf_client.wg_mp_servers[0]["server_profile"] == "ca-tor-mp001.prod.surfshark.com"

def test_update_server_lists_skips_wireguard_multihop_without_pubkey(surf_client):
    """
    Verifies that MultiHop servers without a server public key are not exposed
    as WireGuard options because wg-quick cannot build a valid peer config.
    """
    surf_client.api_servers = [
        {
            "country": "Canada",
            "countryCode": "CA",
            "location": "Toronto",
            "connectionName": "ca-tor-mp001.prod.surfshark.com",
            "endpoint_type": "obfuscated",
            "pubKey": None
        }
    ]

    surf_client.update_server_lists()

    assert surf_client.wg_mp_servers == []
    assert len(surf_client.mp_servers) == 2
