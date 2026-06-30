"""Tests for v1.04 awareness foundation models and schemas."""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from backend.app.models.awareness.device_info import DeviceInfo
from backend.app.models.awareness.file_tracker import FileIndex
from backend.app.models.awareness.project_detector import ProjectIndex
from backend.app.models.awareness.repo_analyzer import RepositoryIndex
from backend.app.models.awareness.system_health import SystemHealth
from backend.app.schemas.awareness.device import DeviceInfoResponse
from backend.app.schemas.awareness.file_tracker import FileChangeSet, FileIndexList, FileIndexResponse
from backend.app.schemas.awareness.health import HealthCheckResponse, SystemHealthResponse
from backend.app.schemas.awareness.project_detector import ProjectIndexResponse
from backend.app.schemas.awareness.repo_analyzer import RepositoryIndexResponse

# ---------------------------------------------------------------------------
# Model creation tests
# ---------------------------------------------------------------------------


class TestFileIndexModel:
    def test_create(self, db_session: Session) -> None:
        f = FileIndex(
            user_id=1,
            file_path="/home/user/project/main.py",
            file_name="main.py",
            file_extension=".py",
            file_size=1024,
            mime_type="text/x-python",
            content_hash="abc123def456",
            parent_directory="/home/user/project",
        )
        db_session.add(f)
        db_session.commit()
        assert f.id is not None
        assert f.file_name == "main.py"
        assert f.content_hash == "abc123def456"

    def test_user_isolation(self, db_session: Session) -> None:
        f1 = FileIndex(user_id=1, file_path="/a.py", file_name="a.py")
        f2 = FileIndex(user_id=2, file_path="/a.py", file_name="a.py")
        db_session.add_all([f1, f2])
        db_session.commit()
        results = db_session.query(FileIndex).filter(FileIndex.user_id == 1).all()
        assert len(results) == 1

    def test_defaults(self, db_session: Session) -> None:
        f = FileIndex(user_id=1, file_path="/x.txt", file_name="x.txt")
        db_session.add(f)
        db_session.commit()
        assert f.indexed_at is not None


class TestRepositoryIndexModel:
    def test_create(self, db_session: Session) -> None:
        r = RepositoryIndex(
            user_id=1,
            repo_path="/home/user/project",
            repo_name="project",
            languages='{"python": 60, "typescript": 40}',
            total_files=100,
            total_lines=5000,
        )
        db_session.add(r)
        db_session.commit()
        assert r.id is not None
        assert r.total_files == 100
        assert r.total_lines == 5000

    def test_user_isolation(self, db_session: Session) -> None:
        r1 = RepositoryIndex(user_id=1, repo_path="/repo1", repo_name="repo1")
        r2 = RepositoryIndex(user_id=2, repo_path="/repo1", repo_name="repo1")
        db_session.add_all([r1, r2])
        db_session.commit()
        results = db_session.query(RepositoryIndex).filter(RepositoryIndex.user_id == 1).all()
        assert len(results) == 1


class TestProjectIndexModel:
    def test_create(self, db_session: Session) -> None:
        p = ProjectIndex(
            user_id=1,
            project_path="/home/user/project",
            project_name="project",
            project_type="python",
            frameworks='["fastapi"]',
            has_tests=1,
        )
        db_session.add(p)
        db_session.commit()
        assert p.project_type == "python"
        assert p.has_tests == 1

    def test_defaults(self, db_session: Session) -> None:
        p = ProjectIndex(user_id=1, project_path="/p", project_name="p")
        db_session.add(p)
        db_session.commit()
        assert p.has_tests == 0
        assert p.has_ci == 0
        assert p.has_docker == 0


class TestDeviceInfoModel:
    def test_create(self, db_session: Session) -> None:
        d = DeviceInfo(
            user_id=1,
            hostname="my-machine",
            os_type="linux",
            os_version="6.1.0",
            cpu_cores=8,
            cpu_model="AMD Ryzen 7",
            total_memory_gb=32,
            available_memory_gb=16,
            disk_total_gb=500,
            disk_used_gb=200,
        )
        db_session.add(d)
        db_session.commit()
        assert d.cpu_cores == 8
        assert d.os_type == "linux"


class TestSystemHealthModel:
    def test_create(self, db_session: Session) -> None:
        h = SystemHealth(
            service_name="database",
            status="healthy",
            response_time_ms=15,
        )
        db_session.add(h)
        db_session.commit()
        assert h.status == "healthy"
        assert h.service_name == "database"


# ---------------------------------------------------------------------------
# Schema validation tests
# ---------------------------------------------------------------------------


class TestSchemas:
    def test_file_index_response(self) -> None:
        s = FileIndexResponse(
            id=1,
            user_id=1,
            file_path="/test.py",
            file_name="test.py",
            indexed_at=datetime.now(timezone.utc),
        )
        assert s.file_name == "test.py"

    def test_file_index_list(self) -> None:
        item = FileIndexResponse(
            id=1,
            user_id=1,
            file_path="/a.py",
            file_name="a.py",
            indexed_at=datetime.now(timezone.utc),
        )
        s = FileIndexList(files=[item], total=1)
        assert len(s.files) == 1

    def test_file_change_set(self) -> None:
        s = FileChangeSet(created=[], modified=[], deleted=["/old.py"], scan_time_ms=42)
        assert s.scan_time_ms == 42

    def test_repository_index_response(self) -> None:
        s = RepositoryIndexResponse(
            id=1,
            user_id=1,
            repo_path="/repo",
            repo_name="repo",
            total_files=10,
            total_lines=500,
            last_indexed=datetime.now(timezone.utc),
        )
        assert s.total_files == 10

    def test_project_index_response(self) -> None:
        s = ProjectIndexResponse(
            id=1,
            user_id=1,
            project_path="/p",
            project_name="p",
            has_tests=0,
            has_ci=0,
            has_docker=0,
            last_scanned=datetime.now(timezone.utc),
        )
        assert s.project_path == "/p"

    def test_device_info_response(self) -> None:
        s = DeviceInfoResponse(
            id=1,
            user_id=1,
            hostname="dev",
            os_type="linux",
            last_checked=datetime.now(timezone.utc),
        )
        assert s.os_type == "linux"

    def test_health_check_response(self) -> None:
        s = HealthCheckResponse(
            id=1,
            service_name="db",
            status="healthy",
            last_check=datetime.now(timezone.utc),
        )
        assert s.status == "healthy"

    def test_system_health_response(self) -> None:
        item = HealthCheckResponse(
            id=1,
            service_name="db",
            status="healthy",
            last_check=datetime.now(timezone.utc),
        )
        s = SystemHealthResponse(
            services=[item],
            overall_status="healthy",
            checked_at=datetime.now(timezone.utc),
        )
        assert s.overall_status == "healthy"
