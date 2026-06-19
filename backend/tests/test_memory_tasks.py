"""Tests for memory background tasks."""
import pytest
from unittest.mock import Mock, patch


@pytest.mark.asyncio
async def test_embed_memory_task():
    from backend.app.tasks.memory_tasks import embed_memory_task

    with patch("backend.app.tasks.memory_tasks.SessionLocal") as mock_session:
        mock_db = Mock()
        mock_session.return_value = mock_db

        with patch("backend.app.tasks.memory_tasks.MemoryManager") as mock_manager:
            mock_instance = Mock()
            mock_manager.return_value = mock_instance
            mock_instance.get.return_value = Mock(id=1)

            result = await embed_memory_task({}, entry_id=1)

            assert result["status"] == "success"
            assert result["entry_id"] == 1
            mock_instance.update.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_embed_memory_task_not_found():
    from backend.app.tasks.memory_tasks import embed_memory_task

    with patch("backend.app.tasks.memory_tasks.SessionLocal") as mock_session:
        mock_db = Mock()
        mock_session.return_value = mock_db

        with patch("backend.app.tasks.memory_tasks.MemoryManager") as mock_manager:
            mock_instance = Mock()
            mock_manager.return_value = mock_instance
            mock_instance.get.return_value = None

            result = await embed_memory_task({}, entry_id=999)

            assert result["status"] == "error"


@pytest.mark.asyncio
async def test_scan_repo_task():
    from backend.app.tasks.memory_tasks import scan_repo_task

    with patch("backend.app.tasks.memory_tasks.SessionLocal") as mock_session:
        mock_db = Mock()
        mock_session.return_value = mock_db

        with patch("backend.app.tasks.memory_tasks.RepoScanner") as mock_scanner:
            mock_instance = Mock()
            mock_scanner.return_value = mock_instance
            mock_instance.scan_repo.return_value = Mock(
                repo_id=1,
                files_scanned=10,
                chunks_created=25,
            )

            result = await scan_repo_task({}, "/path/to/repo", user_id=1)

            assert result["status"] == "success"
            assert result["files_scanned"] == 10
            assert result["chunks_created"] == 25


@pytest.mark.asyncio
async def test_bulk_embed_task():
    from backend.app.tasks.memory_tasks import bulk_embed_task

    with patch("backend.app.tasks.memory_tasks.SessionLocal") as mock_session:
        mock_db = Mock()
        mock_session.return_value = mock_db

        with patch("backend.app.tasks.memory_tasks.MemoryManager") as mock_manager:
            mock_instance = Mock()
            mock_manager.return_value = mock_instance

            result = await bulk_embed_task({}, [1, 2, 3])

            assert result["status"] == "success"
            assert result["total"] == 3
            assert mock_instance.update.call_count == 3
