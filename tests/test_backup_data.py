import pytest
from src.backup_data import list_drives

def test_list_drives():
    drives = list_drives()
    assert isinstance(drives, list)
    # Al menos un elemento en el entorno real