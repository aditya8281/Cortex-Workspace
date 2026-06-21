"""Tests for IndexingOrchestrator."""

import tempfile

import pytest
from sqlalchemy.orm import Session

from backend.app.models.document import Document
from backend.app.services.file_watcher_v2 import FileChange
from backend.app.services.indexing_orchestrator import IndexingOrchestrator


@pytest.fixture()
def mock_doc_indexer():
    class MockDocIndexer:
        def __init__(self):
            self.indexed = []
            self.removed = []
        def index_file(self, path, force=False):
            self.indexed.append(path)
            return True
        def remove_file(self, path):
            self.removed.append(path)
            return True
    return MockDocIndexer()


@pytest.fixture()
def mock_watcher():
    class MockWatcher:
        def __init__(self):
            self._callback = None
            self.watched = set()
        def set_callback(self, cb):
            self._callback = cb
        def watch(self, path):
            self.watched.add(path)
            return True
        def unwatch(self, path):
            self.watched.discard(path)
            return True
        def start(self):
            pass
        def stop(self):
            pass
        def simulate(self, change):
            if self._callback:
                self._callback(change)
    return MockWatcher()


@pytest.fixture()
def orchestrator(db_session, mock_doc_indexer, mock_watcher):
    return IndexingOrchestrator(db_session, document_indexer=mock_doc_indexer, file_watcher=mock_watcher)


def test_routes_markdown_to_doc_indexer(orchestrator, mock_doc_indexer, mock_watcher):
    mock_watcher.simulate(FileChange(path="/repo/readme.md", event_type="created"))
    assert "/repo/readme.md" in mock_doc_indexer.indexed


def test_routes_txt_to_doc_indexer(orchestrator, mock_doc_indexer, mock_watcher):
    mock_watcher.simulate(FileChange(path="/repo/notes.txt", event_type="modified"))
    assert "/repo/notes.txt" in mock_doc_indexer.indexed


def test_routes_deletion(orchestrator, mock_doc_indexer, mock_watcher):
    mock_watcher.simulate(FileChange(path="/repo/old.md", event_type="deleted"))
    assert "/repo/old.md" in mock_doc_indexer.removed


def test_ignores_code_files(orchestrator, mock_doc_indexer, mock_watcher):
    mock_watcher.simulate(FileChange(path="/repo/main.py", event_type="created"))
    assert len(mock_doc_indexer.indexed) == 0
    assert len(mock_doc_indexer.removed) == 0


def test_ignores_unknown_extensions(orchestrator, mock_doc_indexer, mock_watcher):
    mock_watcher.simulate(FileChange(path="/repo/image.png", event_type="created"))
    assert len(mock_doc_indexer.indexed) == 0


def test_start_stop(orchestrator, mock_watcher):
    with tempfile.TemporaryDirectory() as tmpdir:
        orchestrator.start_watching(tmpdir)
        assert tmpdir in mock_watcher.watched
        orchestrator.stop_watching(tmpdir)
        assert tmpdir not in mock_watcher.watched
