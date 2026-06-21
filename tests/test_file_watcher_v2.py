"""Tests for FileWatcherV2."""

import tempfile

from backend.app.services.file_watcher_v2 import FileChange, FileWatcherV2, _ChangeHandler


def test_file_change_dataclass():
    change = FileChange(path="/tmp/test.py", event_type="created")
    assert change.path == "/tmp/test.py"
    assert change.event_type == "created"
    assert change.old_path is None
    assert change.timestamp > 0


def test_watcher_init():
    watcher = FileWatcherV2(debounce_seconds=1.0)
    assert not watcher.is_running
    assert watcher.watched_count == 0


def test_watcher_set_callback():
    watcher = FileWatcherV2()
    called = []
    watcher.set_callback(lambda c: called.append(c))
    assert watcher._on_change is not None


def test_watcher_watch_nonexistent():
    watcher = FileWatcherV2()
    assert not watcher.watch("/nonexistent/path/that/does/not/exist")


def test_handler_ignores_skip_dirs():
    changes = []
    handler = _ChangeHandler(lambda c: changes.append(c), debounce_seconds=0)

    class FakeEvent:
        is_directory = False
        src_path = "/repo/node_modules/package/index.js"

    handler.on_created(FakeEvent())
    assert len(changes) == 0


def test_handler_processes_normal_files():
    changes = []
    handler = _ChangeHandler(lambda c: changes.append(c), debounce_seconds=0)

    class FakeEvent:
        is_directory = False
        src_path = "/repo/src/main.py"

    handler.on_created(FakeEvent())
    assert len(changes) == 1
    assert changes[0].event_type == "created"


def test_handler_debounce():
    changes = []
    handler = _ChangeHandler(lambda c: changes.append(c), debounce_seconds=10)

    class FakeEvent:
        is_directory = False
        src_path = "/repo/src/main.py"

    handler.on_created(FakeEvent())
    handler.on_created(FakeEvent())
    assert len(changes) == 1


def test_handler_move_event():
    changes = []
    handler = _ChangeHandler(lambda c: changes.append(c), debounce_seconds=0)

    class FakeEvent:
        is_directory = False
        src_path = "/repo/old.py"
        dest_path = "/repo/new.py"

    handler.on_moved(FakeEvent())
    assert len(changes) == 1
    assert changes[0].event_type == "moved"
    assert changes[0].old_path == "/repo/old.py"
    assert changes[0].path == "/repo/new.py"


def test_watcher_start_stop():
    watcher = FileWatcherV2()
    with tempfile.TemporaryDirectory() as tmpdir:
        watcher.watch(tmpdir)
        watcher.start()
        assert watcher.is_running
        watcher.stop()
        assert not watcher.is_running
