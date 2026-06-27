"""Project scanner — detects project type, frameworks, configuration, and feature flags."""

from __future__ import annotations

import json
import os
from datetime import datetime

from sqlalchemy.orm import Session

from backend.app.models.awareness.project_detector import ProjectIndex

# Project type detection by config file
PROJECT_TYPE_INDICATORS: dict[str, str] = {
    "package.json": "node",
    "requirements.txt": "python",
    "pyproject.toml": "python",
    "setup.py": "python",
    "Cargo.toml": "rust",
    "go.mod": "go",
    "Gemfile": "ruby",
    "pom.xml": "java",
    "build.gradle": "java",
    "build.gradle.kts": "java",
    "CMakeLists.txt": "cpp",
    "composer.json": "php",
    "pubspec.yaml": "dart",
    "Package.swift": "swift",
    "build.sbt": "scala",
}

# Framework detection by file indicators
FRAMEWORK_INDICATORS: dict[str, list[str]] = {
    # Python
    "manage.py": ["django"],
    "wsgi.py": ["django"],
    "asgi.py": ["fastapi"],
    # Node.js
    "next.config.js": ["next.js"],
    "next.config.mjs": ["next.js"],
    "next.config.ts": ["next.js"],
    "nuxt.config.js": ["nuxt"],
    "nuxt.config.ts": ["nuxt"],
    "gatsby-config.js": ["gatsby"],
    "remix.config.js": ["remix"],
    "vite.config.js": ["vite"],
    "vite.config.ts": ["vite"],
    "angular.json": ["angular"],
    "svelte.config.js": ["svelte"],
    "svelte.config.ts": ["svelte"],
    # Rust
    "Cargo.toml": ["rust"],
    # Go
    "go.mod": ["go"],
}

# Feature detection indicators
FEATURE_INDICATORS: dict[str, list[str]] = {
    "has_tests": [
        "tests/", "test/", "__tests__/", "spec/",
        "pytest.ini", "jest.config.js", "jest.config.ts",
        "vitest.config.ts", "vitest.config.js",
    ],
    "has_ci": [
        ".github/workflows/", ".gitlab-ci.yml",
        ".circleci/", "Jenkinsfile", ".travis.yml",
    ],
    "has_docker": [
        "Dockerfile", "docker-compose.yml", "docker-compose.yaml",
        ".dockerignore",
    ],
}


class ProjectScannerService:
    """Detects project type, frameworks, configuration, and feature flags."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def scan_project(
        self,
        user_id: int,
        project_path: str,
    ) -> ProjectIndex:
        """Scan *project_path* and create/update a ProjectIndex record."""
        project_type = self._detect_type(project_path)
        frameworks = self._detect_frameworks(project_path)
        configuration = self._load_configuration(project_path, project_type)
        features = self._detect_features(project_path)

        existing = (
            self.db.query(ProjectIndex)
            .filter(
                ProjectIndex.user_id == user_id,
                ProjectIndex.project_path == project_path,
            )
            .first()
        )

        if existing is not None:
            existing.project_type = project_type
            existing.frameworks = json.dumps(frameworks)
            existing.configuration = json.dumps(configuration)
            existing.has_tests = features.get("has_tests", 0)
            existing.has_ci = features.get("has_ci", 0)
            existing.has_docker = features.get("has_docker", 0)
            existing.last_scanned = datetime.now()
            self.db.commit()
            self.db.refresh(existing)
            return existing

        project_index = ProjectIndex(
            user_id=user_id,
            project_path=project_path,
            project_name=os.path.basename(project_path),
            project_type=project_type,
            frameworks=json.dumps(frameworks),
            configuration=json.dumps(configuration),
            has_tests=features.get("has_tests", 0),
            has_ci=features.get("has_ci", 0),
            has_docker=features.get("has_docker", 0),
            last_scanned=datetime.now(),
        )
        self.db.add(project_index)
        self.db.commit()
        self.db.refresh(project_index)
        return project_index

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _detect_type(self, project_path: str) -> str:
        """Detect project type from config files."""
        for filename, ptype in PROJECT_TYPE_INDICATORS.items():
            if os.path.exists(os.path.join(project_path, filename)):
                return ptype
        return "unknown"

    def _detect_frameworks(self, project_path: str) -> list[str]:
        """Detect frameworks from file indicators."""
        frameworks: list[str] = []
        for indicator, fw_list in FRAMEWORK_INDICATORS.items():
            if os.path.exists(os.path.join(project_path, indicator)):
                frameworks.extend(fw_list)
        return list(set(frameworks))

    def _detect_features(self, project_path: str) -> dict[str, int]:
        """Detect project features (tests, CI, Docker)."""
        features: dict[str, int] = {}
        for feature, indicators in FEATURE_INDICATORS.items():
            features[feature] = 1 if any(
                os.path.exists(os.path.join(project_path, ind))
                for ind in indicators
            ) else 0
        return features

    def _load_configuration(
        self,
        project_path: str,
        project_type: str,
    ) -> dict[str, object]:
        """Load key configuration values based on project type."""
        if project_type == "python":
            return self._load_python_config(project_path)
        if project_type == "node":
            return self._load_node_config(project_path)
        if project_type == "rust":
            return self._load_rust_config(project_path)
        return {}

    def _load_python_config(self, project_path: str) -> dict[str, object]:
        """Load Python project configuration."""
        config: dict[str, object] = {}

        pyproject = os.path.join(project_path, "pyproject.toml")
        if os.path.exists(pyproject):
            try:
                with open(pyproject) as fh:
                    content = fh.read()
                    if "pytest" in content:
                        config["test_framework"] = "pytest"
                    if "black" in content:
                        config["formatter"] = "black"
                    if "ruff" in content:
                        config["linter"] = "ruff"
            except OSError:
                pass

        req_file = os.path.join(project_path, "requirements.txt")
        if os.path.exists(req_file):
            try:
                with open(req_file) as fh:
                    deps = [
                        line.strip().split("==")[0]
                        for line in fh
                        if line.strip() and not line.startswith("#")
                    ]
                    config["dependency_count"] = len(deps)
            except OSError:
                pass

        return config

    def _load_node_config(self, project_path: str) -> dict[str, object]:
        """Load Node.js project configuration."""
        config: dict[str, object] = {}
        pkg_file = os.path.join(project_path, "package.json")
        if os.path.exists(pkg_file):
            try:
                with open(pkg_file) as fh:
                    pkg = json.load(fh)
                    config["name"] = pkg.get("name", "")
                    config["version"] = pkg.get("version", "")
                    config["node_version"] = pkg.get("engines", {}).get("node", "")
                    config["scripts"] = list(pkg.get("scripts", {}).keys())
            except (json.JSONDecodeError, OSError):
                pass
        return config

    def _load_rust_config(self, project_path: str) -> dict[str, object]:
        """Load Rust project configuration."""
        config: dict[str, object] = {}
        cargo_file = os.path.join(project_path, "Cargo.toml")
        if os.path.exists(cargo_file):
            try:
                with open(cargo_file) as fh:
                    for line in fh:
                        line = line.strip()
                        if line.startswith("name"):
                            config["name"] = line.split("=", 1)[1].strip().strip('"')
                        elif line.startswith("version"):
                            config["version"] = line.split("=", 1)[1].strip().strip('"')
            except OSError:
                pass
        return config
