"""Tests for @tool-decorated tools in tool_defs.py.

Covers the 10 new tools added in V1 Phase 2 (15+ tools target).
"""

from __future__ import annotations

import asyncio
import os
import tempfile
from pathlib import Path

from backend.app.agents.tool_defs import (
    current_datetime,
    get_repo_info,
    git_show,
    git_status,
    grep_files,
    list_available_tools,
    list_directory,
    read_file,
    search_knowledge,
    write_file,
)
from backend.app.agents.tools.registry import get_tool_registry

# ── File tools ─────────────────────────────────────────────────────────


class TestReadFile:
    def setup_method(self):
        self._tmpdir = tempfile.mkdtemp()
        self._orig_env = os.environ.get("AGENT_WORKSPACE")
        os.environ["AGENT_WORKSPACE"] = self._tmpdir
        self._test_file = Path(self._tmpdir) / "hello.txt"
        self._test_file.write_text("line1\nline2\nline3\n", encoding="utf-8")

    def teardown_method(self):
        if self._orig_env is not None:
            os.environ["AGENT_WORKSPACE"] = self._orig_env
        else:
            os.environ.pop("AGENT_WORKSPACE", None)

    def test_read_existing_file(self):
        result = asyncio.run(read_file(path="hello.txt"))
        assert "line1" in result
        assert "line2" in result
        assert "line3" in result

    def test_read_file_not_found(self):
        result = asyncio.run(read_file(path="nope.txt"))
        assert "Error" in result
        assert "not found" in result

    def test_read_file_line_limit(self):
        content = "\n".join(f"line{i}" for i in range(100))
        (Path(self._tmpdir) / "big.txt").write_text(content, encoding="utf-8")
        result = asyncio.run(read_file(path="big.txt", max_lines=10))
        assert "line0" in result
        assert "more lines" in result
        assert "truncated" in result

    def test_read_file_outside_workspace_denied(self):
        result = asyncio.run(read_file(path="/etc/passwd"))
        assert "Error" in result or "traversal" in result.lower()

    def test_read_file_empty(self):
        (Path(self._tmpdir) / "empty.txt").write_text("", encoding="utf-8")
        result = asyncio.run(read_file(path="empty.txt"))
        # Empty file now wrapped with UNTRUSTED_SOURCE_DATA markers
        assert "<UNTRUSTED_SOURCE_DATA" in result
        assert 'source="file:empty.txt"' in result


class TestWriteFile:
    def setup_method(self):
        self._tmpdir = tempfile.mkdtemp()
        self._orig_env = os.environ.get("AGENT_WORKSPACE")
        os.environ["AGENT_WORKSPACE"] = self._tmpdir

    def teardown_method(self):
        if self._orig_env is not None:
            os.environ["AGENT_WORKSPACE"] = self._orig_env
        else:
            os.environ.pop("AGENT_WORKSPACE", None)

    def test_write_new_file(self):
        result = asyncio.run(write_file(path="new.txt", content="hello world"))
        assert "Written" in result
        assert "11 bytes" in result
        written = (Path(self._tmpdir) / "new.txt").read_text(encoding="utf-8")
        assert written == "hello world"

    def test_write_to_subdirectory(self):
        result = asyncio.run(write_file(path="sub/deep/file.txt", content="nested"))
        assert "Written" in result
        target = Path(self._tmpdir) / "sub" / "deep" / "file.txt"
        assert target.read_text(encoding="utf-8") == "nested"

    def test_write_outside_workspace_denied(self):
        result = asyncio.run(write_file(path="/etc/evil.txt", content="bad"))
        assert "Error" in result or "denied" in result.lower()


class TestListDirectory:
    def setup_method(self):
        self._tmpdir = tempfile.mkdtemp()
        self._orig_env = os.environ.get("AGENT_WORKSPACE")
        os.environ["AGENT_WORKSPACE"] = self._tmpdir
        (Path(self._tmpdir) / "file_a.txt").write_text("a", encoding="utf-8")
        (Path(self._tmpdir) / "file_b.txt").write_text("b" * 100, encoding="utf-8")
        (Path(self._tmpdir) / "subdir").mkdir()

    def teardown_method(self):
        if self._orig_env is not None:
            os.environ["AGENT_WORKSPACE"] = self._orig_env
        else:
            os.environ.pop("AGENT_WORKSPACE", None)

    def test_list_directory_root(self):
        result = asyncio.run(list_directory(path="."))
        assert "file_a.txt" in result
        assert "file_b.txt" in result
        assert "subdir/" in result

    def test_list_nonexistent(self):
        result = asyncio.run(list_directory(path="nope"))
        assert "not found" in result

    def test_list_empty_directory(self):
        empty = Path(self._tmpdir) / "empty_dir"
        empty.mkdir()
        result = asyncio.run(list_directory(path="empty_dir"))
        assert "empty directory" in result or "(empty directory)" in result

    def test_list_outside_workspace_denied(self):
        result = asyncio.run(list_directory(path="/tmp"))
        assert "Error" in result or "denied" in result.lower() or "traversal" in result.lower()


class TestGrepFiles:
    def setup_method(self):
        self._tmpdir = tempfile.mkdtemp()
        self._orig_env = os.environ.get("AGENT_WORKSPACE")
        os.environ["AGENT_WORKSPACE"] = self._tmpdir
        (Path(self._tmpdir) / "src").mkdir()
        (Path(self._tmpdir) / "src" / "main.py").write_text(
            "def hello():\n    print('hello world')\n\ndef bye():\n    pass\n",
            encoding="utf-8",
        )
        (Path(self._tmpdir) / "src" / "utils.py").write_text(
            "import os\n\ndef helper():\n    return os.path.join('a', 'b')\n",
            encoding="utf-8",
        )

    def teardown_method(self):
        if self._orig_env is not None:
            os.environ["AGENT_WORKSPACE"] = self._orig_env
        else:
            os.environ.pop("AGENT_WORKSPACE", None)

    def test_grep_finds_match(self):
        result = asyncio.run(grep_files(pattern="def ", path=".", max_results=50))
        assert "Found" in result
        assert "main.py" in result
        assert "utils.py" in result

    def test_grep_no_match(self):
        result = asyncio.run(grep_files(pattern="ZZZZNOSUCHPATTERN", path=".", max_results=50))
        assert "No matches" in result

    def test_grep_invalid_regex(self):
        result = asyncio.run(grep_files(pattern="[unclosed", path=".", max_results=50))
        assert "Error" in result
        assert "regex" in result.lower()

    def test_grep_nonexistent_path(self):
        result = asyncio.run(grep_files(pattern="test", path="/nonexistent", max_results=50))
        assert "not found" in result or "traversal" in result.lower()


# ── Git tools ──────────────────────────────────────────────────────────


class TestGitStatus:
    def test_git_status(self):
        result = asyncio.run(git_status())
        # Should either show status or "(clean working tree)"
        assert isinstance(result, str)
        assert len(result) > 0


class TestGitShow:
    def test_git_show_head(self):
        result = asyncio.run(git_show(ref="HEAD"))
        assert "Author:" in result or "Subject:" in result or "bad object" in result.lower() or "error" in result

    def test_git_show_invalid_ref(self):
        result = asyncio.run(git_show(ref="NONEXISTENT_REF_12345"))
        assert "Error" in result or "git error" in result


class TestGetRepoInfo:
    def test_get_repo_info(self):
        result = asyncio.run(get_repo_info())
        assert "Repository:" in result
        assert "Branch:" in result
        assert "git not available" not in result.lower()


# ── Knowledge search ───────────────────────────────────────────────────


class TestSearchKnowledge:
    def test_search_knowledge(self):
        """Knowledge search may not be available in all test environments.
        Should handle gracefully either way."""
        result = asyncio.run(search_knowledge(query="test", limit=5))
        # Either returns results, no results message, or graceful error
        assert isinstance(result, str)
        assert len(result) > 0


# ── System tools ───────────────────────────────────────────────────────


class TestCurrentDatetime:
    def test_current_datetime_format(self):
        result = asyncio.run(current_datetime())
        assert "UTC" in result
        assert "20" in result  # year 20xx

    def test_current_datetime_contains_separators(self):
        result = asyncio.run(current_datetime())
        assert ":" in result  # time separator
        assert "-" in result  # date separator


class TestListAvailableTools:
    def test_lists_tools(self):
        result = asyncio.run(list_available_tools())
        assert "Available tools" in result or "No tools" in result

    def test_contains_known_tools(self):
        result = asyncio.run(list_available_tools())
        # Should list at least some of the registered tools
        assert "exec_command" in result or "read_file" in result

    def test_count_at_least_15(self):
        """V1 Phase 2 requires 15+ tools registered."""
        registry = get_tool_registry()
        assert registry.count >= 15, f"Only {registry.count} tools registered, need 15+"


# ── Integration: all tools have schemas ────────────────────────────────


class TestAllToolsHaveSchemas:
    def test_all_registered_tools_have_schemas(self):
        """Every @tool-decorated tool should have an auto-generated schema."""
        registry = get_tool_registry()
        no_schema: list[str] = []
        for t in registry.get_all():
            # list_available_tools and some system tools intentionally skip schema
            # where auto_schema=False, but most should have one
            if not t.schema and t.name not in ("list_available_tools",):
                no_schema.append(t.name)
        assert not no_schema, f"Tools missing schema: {no_schema}"

    def test_15_tools_registered(self):
        """Verify 15+ tools are in the registry."""
        registry = get_tool_registry()
        assert registry.count >= 15, f"Got {registry.count}, need 15+"
