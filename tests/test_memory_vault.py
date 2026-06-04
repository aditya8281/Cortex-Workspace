import os
import shutil
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from backend.app.services.memory_manager import memory_manager


@pytest.fixture(autouse=True)
def setup_test_vault(tmp_path):
    # Setup temporary config file and redirect memory manager to use it
    original_config_file = memory_manager._config_file
    test_config_file = tmp_path / ".cortex_memory_path"
    memory_manager._config_file = test_config_file
    
    # Store original memory path
    try:
        original_path = memory_manager.get_memory_path()
    except Exception:
        original_path = Path("~/cortex_memory").expanduser().resolve()
        
    # Redirect to a temporary test memory vault directory
    test_vault_path = tmp_path / "cortex_memory"
    memory_manager.set_memory_path(str(test_vault_path))
    memory_manager.ensure_vault_structure()
    
    yield test_vault_path
    
    # Cleanup config file
    if test_config_file.exists():
        test_config_file.unlink()
        
    # Restore original config file and path
    memory_manager._config_file = original_config_file
    if original_config_file.exists():
        try:
            memory_manager.set_memory_path(str(original_path))
        except Exception:
            pass


def test_default_structure(setup_test_vault):
    vault_path = setup_test_vault
    assert vault_path.exists()
    assert vault_path.is_dir()
    
    # Verify all categories are present as subfolders
    for cat in memory_manager.CATEGORIES:
        cat_dir = vault_path / cat
        assert cat_dir.exists()
        assert cat_dir.is_dir()


def test_validation_boundaries(setup_test_vault):
    # Verify system path validation block
    for sys_path in ["/sys", "/etc", "/dev", "/proc", "/boot", "/root"]:
        with pytest.raises(ValueError, match="Security exception"):
            memory_manager.validate_memory_path(Path(sys_path))

    # Verify traversal block in get_path
    with pytest.raises(PermissionError, match="Security Violation"):
        memory_manager.get_path("sync_state", "../../escaped.txt")


def test_read_write_abstractions(setup_test_vault):
    filename = "test_config.json"
    content = '{"key": "value"}'
    
    # Write
    memory_manager.write_text("sync_state", filename, content)
    
    # Check exists
    assert memory_manager.exists("sync_state", filename)
    
    # Read
    read_val = memory_manager.read_text("sync_state", filename)
    assert read_val == content
    
    # List files
    files = memory_manager.list_files("sync_state")
    assert filename in files
    
    # Delete
    memory_manager.delete_file("sync_state", filename)
    assert not memory_manager.exists("sync_state", filename)


def test_vault_migration(setup_test_vault, tmp_path):
    old_vault = setup_test_vault
    new_vault = tmp_path / "cortex_memory_new"
    
    # Write some dummy test file to old vault
    memory_manager.write_text("sync_state", "profile.json", "cortex-settings")
    
    # Re-mock session/engine resets to prevent sql connections during test
    with patch("backend.app.db.session.reset_db_engine"), \
         patch("backend.app.db.session.run_migrations"):
        
        # Change vault path
        memory_manager.change_memory_vault(str(new_vault))
        
        # Verify new path is configured
        assert memory_manager.get_memory_path() == new_vault
        
        # Verify folder structure is initialized in new path
        for cat in memory_manager.CATEGORIES:
            assert (new_vault / cat).exists()
            
        # Verify files were migrated/copied
        assert (new_vault / "sync_state" / "profile.json").exists()
        assert (new_vault / "sync_state" / "profile.json").read_text(encoding="utf-8") == "cortex-settings"


def test_vault_export_import(setup_test_vault, tmp_path):
    vault_path = setup_test_vault
    backup_zip = tmp_path / "backup.zip"
    
    # Write test file
    memory_manager.write_text("embeddings", "doc_vector.bin", "vector-bytes")
    
    # Re-mock session/engine resets to prevent sql connections during test
    with patch("backend.app.db.session.reset_db_engine"), \
         patch("backend.app.db.session.run_migrations"):
         
        # Export vault to zip
        memory_manager.export_memory(str(backup_zip))
        assert backup_zip.exists()
        assert backup_zip.is_file()
        
        # Modify current vault to simulate state changes
        memory_manager.write_text("embeddings", "doc_vector.bin", "new-vector-bytes")
        
        # Import vault from backup
        memory_manager.import_memory(str(backup_zip))
        
        # Verify content was restored to the backup version
        assert memory_manager.read_text("embeddings", "doc_vector.bin") == "vector-bytes"
