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
