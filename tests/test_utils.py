"""
Unit tests for the Utils class helper methods.
"""

import pytest
import os
from src.utils import Utils

def test_get_available_connection_types():
    """
    Verifies that the connection types list is correctly structured
    and contains the expected actions.
    """
    conn_types = Utils.get_available_connection_types()
    
    assert isinstance(conn_types, list)
    assert len(conn_types) == 9
    
    actions = [c["action"] for c in conn_types]
    assert "wg" in actions
    assert "wg_mp" in actions
    assert "st_udp" in actions
    assert "mp_tcp" in actions
    
    # Check required keys in each dictionary
    for ct in conn_types:
        assert "name" in ct
        assert "description" in ct
        assert "action" in ct

def test_get_path():
    """
    Verifies that get_path correctly constructs absolute paths
    relative to the project root.
    """
    path = Utils.get_path("test.txt")
    assert os.path.isabs(path)
    assert path.endswith("test.txt")
