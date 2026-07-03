"""Agent tool implementations with approval flags.

Legacy TOOL_REGISTRY + new @tool decorator system.
Both systems are maintained during V1 Phase-2 transition.
"""

from __future__ import annotations

import asyncio
import logging
import os
import shlex
from pathlib import Path
from typing import Any

from backend.app.agents.security import wrap_external_content
from backend.app.agents.tools.registry import tool
from backend.app.agents.tools.security import (
    BLOCKED_URL_SCHEMES,
    ensure_within_workspace,
    has_blocked_command,
    is_private_url,
)

# Re-export with legacy names for backward compat during V1 Phase-2 transition.
# After executor.py is replaced by the streaming loop, remove these aliases.
_is_private_url = is_private_url

logger = logging.getLogger(__name__)

AGENT_WORKSPACE = os.environ.get(
    "AGENT_WORKSPACE",
    os.path.join(os.path.expanduser("~"), ".cortex-agent-workspace"),
)


class UserInputRequired(Exception):
    """Raised when the agent needs user input to proceed."""

    def __init__(self, prompt: str):
        self.prompt = prompt
        super().__init__(prompt)


TOOL_REGISTRY: dict[str, dict[str, Any]] = {}

_REQUIRES_APPROVAL = {"exec_command", "write_file", "web_fetch"}


def requires_approval(tool_name: str) -> bool:
    return tool_name in _REQUIRES_APPROVAL


def register_tool(name: str, handler: Any, description: str = "") -> None:
    TOOL_REGISTRY[name] = {"handler": handler, "description": description}


def get_tool(name: str) -> Any | None:
    entry = TOOL_REGISTRY.get(name)
    return entry["handler"] if entry else None


def list_tools() -> dict[str, str]:
    return {name: entry["description"] for name, entry in TOOL_REGISTRY.items()}


@tool(description="Run a shell command with safety limits", requires_approval=True, category="system")
async def exec_command(command: str) -> str:
    """Execute a shell command safely with safety limits and timeout.

    Args:
        command: The shell command to execute
    """
    command = command.strip()
    if not command:
        raise ValueError("Command is required")

    blocked = has_blocked_command(command)
    if blocked:
        raise ValueError(f"Blocked dangerous command pattern: {blocked}")

    try:
        parts = shlex.split(command)
    except ValueError:
        return f"Error: malformed quoting in command — {command}"

    workspace = Path(AGENT_WORKSPACE).resolve()
    workspace.mkdir(parents=True, exist_ok=True)

    proc = await asyncio.create_subprocess_exec(
        *parts,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=str(workspace),
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
    except asyncio.TimeoutError:
        proc.kill()
        return "Command timed out after 30 seconds"

    output = (stdout or b"").decode("utf-8", errors="replace")[:10240]
    err = (stderr or b"").decode("utf-8", errors="replace")[:2048]

    if proc.returncode != 0:
        return f"Exit {proc.returncode}\n{err}\n{output}".strip()
    return output or "(no output)"


@tool(description="Show recent git commits", category="code")
async def git_log(count: int = 10) -> str:
    """Show recent git commits.

    Args:
        count: Number of recent commits to show
    """
    try:
        proc = await asyncio.create_subprocess_exec(
            "git",
            "log",
            "--oneline",
            f"-{count}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=10)
        output = stdout.decode("utf-8", errors="replace")
        if proc.returncode != 0:
            return f"git error: {stderr.decode('utf-8', errors='replace')}"
        return output.strip() or "No commits found"
    except asyncio.TimeoutError:
        return "Error: git log timed out"
    except FileNotFoundError:
        return "Error: git not available"


@tool(description="Show file changes (git diff)", category="code")
async def git_diff(file_path: str | None = None) -> str:
    """Show file changes (git diff).

    Args:
        file_path: Optional specific file to diff
    """
    try:
        if file_path and file_path.startswith("-"):
            return "Error: invalid file path"
        args = ["git", "diff"]
        if file_path:
            args.append(file_path)
        proc = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=10)
        output = stdout.decode("utf-8", errors="replace")
        if proc.returncode != 0:
            return f"git error: {stderr.decode('utf-8', errors='replace')}"
        return output.strip() or "No changes"
    except asyncio.TimeoutError:
        return "Error: git diff timed out"
    except FileNotFoundError:
        return "Error: git not available"


@tool(description="Fetch URL content (max 100KB)", requires_approval=True, category="web")
async def web_fetch(url: str) -> str:
    """Fetch URL content (max 100KB).

    Args:
        url: The URL to fetch
    """
    if any(url.lower().startswith(s) for s in BLOCKED_URL_SCHEMES):
        return f"Error: URL scheme not allowed: {url}"

    if _is_private_url(url):
        return "Error: SSRF protection — URL targets a private/internal network and is blocked"

    try:
        import urllib.request

        req = urllib.request.Request(url, headers={"User-Agent": "Cortex-Agent/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read(100 * 1024)
            content = data.decode("utf-8", errors="replace")
            return wrap_external_content(content, source=f"web:{url}")
    except Exception as e:
        return f"Error fetching URL: {e}"


@tool(description="Ask user for input — raises a signal for the run manager to handle", category="system")
async def ask_user(question: str) -> str:
    """Ask user for input. Raises UserInputRequired for run manager to handle.

    Args:
        question: The question to ask the user
    """
    raise UserInputRequired(question)


# ---------------------------------------------------------------------------
# New tools (V1 Phase 2 — 15+ tools target)
# ---------------------------------------------------------------------------


@tool(description="Read file contents with line limit", category="files")
async def read_file(path: str, max_lines: int = 500) -> str:
    """Read the contents of a file, limited to max_lines.

    Args:
        path: Absolute path or path relative to workspace root
        max_lines: Maximum number of lines to read (default 500)
    """
    try:
        target = ensure_within_workspace(path)
    except (ValueError, PermissionError) as exc:
        return f"Error: {exc}"
    if not target.exists():
        return f"Error: file not found — {path}"
    if not target.is_file():
        return f"Error: not a file — {path}"
    try:
        text = target.read_text("utf-8", errors="replace")
        lines = text.split("\n")
        total = len(lines)
        if total > max_lines:
            shown = lines[:max_lines]
            text = "\n".join(shown)
            text += f"\n\n... ({total - max_lines} more lines, truncated at {max_lines})"
        return wrap_external_content(text, source=f"file:{path}")
    except PermissionError:
        return f"Error: permission denied — {path}"
    except Exception as exc:
        return f"Error reading file: {exc}"


@tool(description="Write content to a file (requires approval)", requires_approval=True, category="files")
async def write_file(path: str, content: str) -> str:
    """Write content to a file. Absolute paths go anywhere in your home
    directory; relative paths are restricted to the agent workspace.

    Args:
        path: Absolute path (e.g. ~/Desktop/file.py) or path relative to workspace
        content: The content to write
    """
    try:
        target = ensure_within_workspace(path)
    except (ValueError, PermissionError) as exc:
        return f"Error: {exc}"
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        target.write_text(content, encoding="utf-8")
        return f"Written {len(content)} bytes to {target}"
    except PermissionError:
        return f"Error: permission denied — {path}"
    except Exception as exc:
        return f"Error writing file: {exc}"


@tool(description="List directory contents", category="files")
async def list_directory(path: str = ".") -> str:
    """List files and directories at the given path.

    Args:
        path: Directory path relative to workspace root (default: .)
    """
    try:
        target = ensure_within_workspace(path)
    except (ValueError, PermissionError) as exc:
        return f"Error: {exc}"
    if not target.exists():
        return f"Error: path not found — {path}"
    if not target.is_dir():
        return f"Error: not a directory — {path}"
    try:
        entries = sorted(target.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        lines: list[str] = []
        for entry in entries:
            suffix = "/" if entry.is_dir() else ""
            size = entry.stat().st_size if entry.is_file() else 0
            if entry.is_file():
                lines.append(f"  {entry.name}{suffix}  ({size} bytes)")
            else:
                lines.append(f"  {entry.name}{suffix}")
        if not lines:
            return "(empty directory)"
        return "\n".join(lines)
    except PermissionError:
        return f"Error: permission denied — {path}"
    except Exception as exc:
        return f"Error listing directory: {exc}"


@tool(description="Find a file or directory by name on the filesystem", category="files")
async def search_path(name: str, start_dir: str = "~", max_depth: int = 3) -> str:
    """Search for a file or directory by name on the filesystem.

    Walks the directory tree starting from start_dir (default: home directory),
    looking for files/directories whose name matches the query.

    Args:
        name: Filename or directory name to search for (case-insensitive substring)
        start_dir: Directory to start searching from (default: ~)
        max_depth: Maximum directory depth to search (default 3, max 6)
    """
    max_depth = min(max_depth, 6)
    try:
        start = Path(start_dir).expanduser().resolve()
    except Exception as exc:
        return f"Error: invalid start directory — {exc}"

    if not start.exists() or not start.is_dir():
        return f"Error: start directory not found — {start_dir}"

    matches: list[str] = []
    query = name.lower()

    try:
        for root, dirs, files in os.walk(str(start)):
            rel = Path(root).relative_to(start)
            depth = len(rel.parts) if str(rel) != "." else 0
            if depth > max_depth:
                dirs.clear()
                continue

            # Check current directory name
            if query in Path(root).name.lower():
                matches.append(f"[dir]  {root}")

            # Check files
            for fname in files:
                if query in fname.lower():
                    matches.append(f"[file] {os.path.join(root, fname)}")

            # Limit to most relevant results
            if len(matches) >= 30:
                break

        if not matches:
            return f"No results found for \"{name}\" in {start_dir} (depth={max_depth})"

        summary = f"Found {len(matches)} result{'s' if len(matches) != 1 else ''} for \"{name}\" in {start_dir}:\n"
        return summary + "\n".join(matches[:25])
    except PermissionError:
        return f"Permission denied while searching — some directories may be restricted"
    except Exception as exc:
        return f"Error searching: {exc}"


@tool(description="Search for text patterns in files (like grep)", category="code")
async def grep_files(pattern: str, path: str = ".", max_results: int = 50) -> str:
    """Search for a regex pattern in files within the given directory.

    Args:
        pattern: Regex pattern to search for
        path: Directory to search in (relative to workspace root)
        max_results: Maximum match lines to return (default 50)
    """
    try:
        target = ensure_within_workspace(path)
    except (ValueError, PermissionError) as exc:
        return f"Error: {exc}"
    if not target.exists():
        return f"Error: path not found — {path}"
    if not target.is_dir():
        return f"Error: not a directory — {path}"

    import re

    try:
        compiled = re.compile(pattern)
    except re.error as exc:
        return f"Error: invalid regex pattern — {exc}"

    matches: list[tuple[str, int, str]] = []
    try:
        for file_path in target.rglob("*"):
            if not file_path.is_file():
                continue
            # Skip binary and hidden
            if file_path.name.startswith("."):
                continue
            ext = file_path.suffix.lower()
            if ext in (".pyc", ".pyo", ".so", ".dll", ".dylib", ".exe", ".bin", ".o", ".a"):
                continue

            try:
                text = file_path.read_text("utf-8", errors="replace")
                for i, line in enumerate(text.split("\n"), 1):
                    if compiled.search(line):
                        rel_path = str(file_path.relative_to(target))
                        matches.append((rel_path, i, line.strip()[:200]))
                        if len(matches) >= max_results:
                            break
            except (PermissionError, UnicodeDecodeError):
                continue
            if len(matches) >= max_results:
                break
    except Exception as exc:
        return f"Error searching files: {exc}"

    if not matches:
        return f"No matches found for: {pattern}"

    result_parts: list[str] = [f"Found {len(matches)} match(es) for: {pattern}"]
    for fpath, lineno, line in matches[:max_results]:
        result_parts.append(f"  {fpath}:{lineno}: {line}")
    return wrap_external_content("\n".join(result_parts), source=f"grep:{path}:{pattern}")


@tool(description="Show git working tree status", category="code")
async def git_status() -> str:
    """Show the git working tree status (modified, staged, untracked files)."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "git",
            "status",
            "--short",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=10)
        output = stdout.decode("utf-8", errors="replace")
        if proc.returncode != 0:
            return f"git error: {stderr.decode('utf-8', errors='replace')}"
        if not output.strip():
            return "(clean working tree)"
        return output.strip()
    except asyncio.TimeoutError:
        return "Error: git status timed out"
    except FileNotFoundError:
        return "Error: git not available"


@tool(description="Show git commit details or file content from a commit", category="code")
async def git_show(ref: str = "HEAD") -> str:
    """Show details of a git commit or object.

    Args:
        ref: Git reference (commit hash, branch, tag). Default: HEAD
    """
    try:
        proc = await asyncio.create_subprocess_exec(
            "git",
            "show",
            "--stat",
            "--pretty=format:%H%nAuthor: %an <%ae>%nDate: %ad%nSubject: %s%n%b",
            ref,
            "--",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=10)
        output = stdout.decode("utf-8", errors="replace")
        if proc.returncode != 0:
            return f"git error: {stderr.decode('utf-8', errors='replace')}"
        return output.strip() or f"No output for ref: {ref}"
    except asyncio.TimeoutError:
        return "Error: git show timed out"
    except FileNotFoundError:
        return "Error: git not available"


# (moved to V1 Phase 3 section below — search_knowledge with relevance filtering)


@tool(description="Get the current date and time", category="system")
async def current_datetime() -> str:
    """Get the current date and time. Useful when the agent needs to know what
    time it is or what day/date it is."""
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    return now.strftime("%Y-%m-%d %H:%M:%S UTC")


@tool(description="List all available tools with descriptions", category="system")
async def list_available_tools() -> str:
    """List all registered tools with their descriptions and parameter info."""
    from backend.app.agents.tools.registry import get_tool_registry

    registry = get_tool_registry()
    all_tools = registry.get_all()
    if not all_tools:
        return "No tools registered."
    lines: list[str] = [f"Available tools ({len(all_tools)}):"]
    for t in all_tools:
        req = " [requires approval]" if t.requires_approval else ""
        params = ""
        try:
            props = t.schema.get("function", {}).get("parameters", {}).get("properties", {})
            if props:
                param_names = ", ".join(props.keys())
                params = f" ({param_names})"
        except Exception:
            pass
        lines.append(f"  - {t.name}: {t.description}{params}{req}")
    return "\n".join(lines)



@tool(description="Get repository information", category="code")
async def get_repo_info() -> str:
    """Get information about the current git repository: name, branch, remote URL."""
    try:
        # Get repo root
        proc_root = await asyncio.create_subprocess_exec(
            "git",
            "rev-parse",
            "--show-toplevel",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout_root, _ = await asyncio.wait_for(proc_root.communicate(), timeout=5)
        root = stdout_root.decode("utf-8", errors="replace").strip()
        if proc_root.returncode != 0:
            root = "(not a git repo or git not available)"

        # Get branch
        proc_branch = await asyncio.create_subprocess_exec(
            "git",
            "branch",
            "--show-current",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout_branch, _ = await asyncio.wait_for(proc_branch.communicate(), timeout=5)
        branch = stdout_branch.decode("utf-8", errors="replace").strip() or "(detached HEAD)"

        # Get remote URL
        proc_remote = await asyncio.create_subprocess_exec(
            "git",
            "remote",
            "get-url",
            "origin",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout_remote, _ = await asyncio.wait_for(proc_remote.communicate(), timeout=5)
        remote = (
            stdout_remote.decode("utf-8", errors="replace").strip() if proc_remote.returncode == 0 else "(no remote)"
        )

        repo_name = root.split("/")[-1] if "/" in root else root
        return f"Repository: {repo_name}\nBranch: {branch}\nRemote: {remote}\nRoot: {root}"
    except asyncio.TimeoutError:
        return "Error: git commands timed out"
    except FileNotFoundError:
        return "Error: git not available"


# ═══════════════════════════════════════════════════════════════════════════
# V1 Phase 3 — new tools
# ═══════════════════════════════════════════════════════════════════════════


@tool(description="Edit an existing file by replacing exact text (requires approval)", requires_approval=True, category="files")
async def edit_file(path: str, old_string: str, new_string: str, replace_all: bool = False) -> str:
    """Edit a file by replacing exact occurrences of old_string with new_string.
    Like Claude Code's edit — precise, targeted changes without rewriting the whole file.

    Args:
        path: Absolute path or path relative to workspace root
        old_string: The exact text to find and replace (must match exactly)
        new_string: The replacement text
        replace_all: If True, replace ALL occurrences. Default: only the first.
    """
    try:
        target = ensure_within_workspace(path)
    except (ValueError, PermissionError) as exc:
        return f"Error: {exc}"

    if not target.exists():
        return f"Error: file not found — {path}"
    if not target.is_file():
        return f"Error: not a file — {path}"

    try:
        content = target.read_text("utf-8", errors="replace")
    except PermissionError:
        return f"Error: permission denied — {path}"
    except Exception as exc:
        return f"Error reading file: {exc}"

    if old_string not in content:
        return f"Error: old_string not found in file. Use read_file to see current content."

    if replace_all:
        new_content = content.replace(old_string, new_string)
        count = content.count(old_string)
    else:
        new_content = content.replace(old_string, new_string, 1)
        count = 1

    try:
        target.write_text(new_content, encoding="utf-8")
        old_len = len(old_string)
        new_len = len(new_string)
        return (
            f"Edited {path}: replaced {count} occurrence(s) "
            f"({old_len} chars -> {new_len} chars)"
        )
    except PermissionError:
        return f"Error: permission denied — {path}"
    except Exception as exc:
        return f"Error writing file: {exc}"


@tool(description="Copy a file or directory (requires approval)", requires_approval=True, category="files")
async def copy_file(source: str, destination: str) -> str:
    """Copy a file or directory from source to destination.

    Args:
        source: Path to the source file or directory
        destination: Path to the destination
    """
    try:
        src = ensure_within_workspace(source)
        dst = ensure_within_workspace(destination)
    except (ValueError, PermissionError) as exc:
        return f"Error: {exc}"

    if not src.exists():
        return f"Error: source not found — {source}"

    import shutil as _shutil

    try:
        if src.is_dir():
            _shutil.copytree(src, dst, dirs_exist_ok=True)
            return f"Copied directory {source} -> {destination}"
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            _shutil.copy2(src, dst)
            return f"Copied file {source} -> {destination} ({dst.stat().st_size} bytes)"
    except PermissionError:
        return f"Error: permission denied"
    except Exception as exc:
        return f"Error copying: {exc}"


@tool(description="Move or rename a file or directory (requires approval)", requires_approval=True, category="files")
async def move_file(source: str, destination: str) -> str:
    """Move or rename a file or directory.

    Args:
        source: Path to the source file or directory
        destination: Path to the destination
    """
    try:
        src = ensure_within_workspace(source)
        dst = ensure_within_workspace(destination)
    except (ValueError, PermissionError) as exc:
        return f"Error: {exc}"

    if not src.exists():
        return f"Error: source not found — {source}"

    try:
        dst.parent.mkdir(parents=True, exist_ok=True)
        src.rename(dst)
        return f"Moved {source} -> {destination}"
    except PermissionError:
        return f"Error: permission denied"
    except Exception as exc:
        return f"Error moving: {exc}"


@tool(description="Delete a file or empty directory (requires approval)", requires_approval=True, category="files")
async def delete_file(path: str) -> str:
    """Delete a file or empty directory.

    Args:
        path: Path to the file or directory to delete
    """
    try:
        target = ensure_within_workspace(path)
    except (ValueError, PermissionError) as exc:
        return f"Error: {exc}"

    if not target.exists():
        return f"Error: path not found — {path}"

    try:
        if target.is_dir():
            # Only delete empty directories via this tool (safety)
            target.rmdir()
            return f"Deleted empty directory: {path}"
        else:
            size = target.stat().st_size
            target.unlink()
            return f"Deleted file: {path} ({size} bytes)"
    except OSError as exc:
        return f"Error: {exc}"
    except PermissionError:
        return f"Error: permission denied — {path}"
    except Exception as exc:
        return f"Error deleting: {exc}"


@tool(description="Create a directory (including parents)", category="files")
async def mkdir(path: str) -> str:
    """Create a directory and any missing parent directories.

    Args:
        path: Path to the directory to create
    """
    try:
        target = ensure_within_workspace(path)
    except (ValueError, PermissionError) as exc:
        return f"Error: {exc}"

    if target.exists():
        return f"Directory already exists: {path}"

    try:
        target.mkdir(parents=True, exist_ok=True)
        return f"Created directory: {path}"
    except PermissionError:
        return f"Error: permission denied — {path}"
    except Exception as exc:
        return f"Error creating directory: {exc}"


@tool(
    description="Search the web with automatic content extraction",
    category="web",
)
async def web_search(query: str, max_results: int = 5) -> str:
    """Search the web, extract content from top result pages, and return
    synthesized information with sources.

    Tries multiple backends:
    1. DuckDuckGo Instant Answer API (no CAPTCHA)
    2. DuckDuckGo HTML search (full results)
    3. Google fallback

    After finding results, automatically fetches top pages and extracts
    their readable text content so the model can reference real data.

    Args:
        query: The search query
        max_results: Maximum number of results to return (default 5, max 10)
    """
    import json as _json
    import re as _re
    import urllib.parse as _uparse
    import urllib.request as _ureq

    max_results = min(max_results, 10)

    def _fetch(url: str, timeout: int = 8) -> str | None:
        try:
            req = _ureq.Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:134.0) Gecko/20100101 Firefox/134.0",
                },
            )
            with _ureq.urlopen(req, timeout=timeout) as r:
                return r.read(200 * 1024).decode("utf-8", errors="replace")
        except Exception:
            return None

    def _is_captcha(html: str) -> bool:
        return bool(_re.search(r"anomaly-modal|challenge|captcha|unfortunately.*bot", html, _re.I))

    def _ddg_redirect_url(ddg_url: str) -> str:
        q_pos = ddg_url.find("uddg=")
        if q_pos == -1:
            return ddg_url
        encoded = ddg_url[q_pos + 5:]
        amp_pos = encoded.find("&")
        if amp_pos != -1:
            encoded = encoded[:amp_pos]
        try:
            return _uparse.unquote(encoded)
        except Exception:
            return ddg_url

    def _extract_readable_text(html: str) -> str:
        """Strip HTML tags and extract readable text from a page."""
        # Remove script and style blocks
        html = _re.sub(r"<script[^>]*>.*?</script>", "", html, flags=_re.DOTALL)
        html = _re.sub(r"<style[^>]*>.*?</style>", "", html, flags=_re.DOTALL)
        html = _re.sub(r"<nav[^>]*>.*?</nav>", "", html, flags=_re.DOTALL)
        html = _re.sub(r"<footer[^>]*>.*?</footer>", "", html, flags=_re.DOTALL)
        # Replace tags with newlines
        html = _re.sub(r"<br\s*/?>", "\n", html)
        html = _re.sub(r"</(p|div|h[1-6]|li|tr|blockquote)>", "\n", html)
        # Strip remaining tags
        text = _re.sub(r"<[^>]+>", "", html)
        # Collapse whitespace
        text = _re.sub(r"\n{3,}", "\n\n", text)
        text = _re.sub(r" {2,}", " ", text)
        return text.strip()[:5000]

    encoded = _uparse.quote_plus(query)
    found_results: list[dict[str, str]] = []

    # ── Path 1: DuckDuckGo Instant Answer API ──────────────────────────────
    ddg_api_url = f"https://api.duckduckgo.com/?q={encoded}&format=json&no_html=1"
    api_html = _fetch(ddg_api_url)
    if api_html:
        try:
            data = _json.loads(api_html)
            abstract = data.get("Abstract", "") or ""
            answer = data.get("Answer", "") or ""
            heading = data.get("Heading", "") or ""

            if answer:
                found_results.append({"title": heading or "Answer", "url": "", "snippet": answer})
            if abstract and not answer:
                url = data.get("AbstractURL", "") or ""
                found_results.append({"title": heading or "Result", "url": url, "snippet": abstract[:500]})
            for topic in data.get("RelatedTopics", []):
                if isinstance(topic, dict):
                    text = topic.get("Text", "") or ""
                    t_url = topic.get("FirstURL", "") or ""
                    if text:
                        found_results.append({"title": text[:80], "url": t_url, "snippet": text[:300]})
                    for ct in topic.get("Topics", [])[:3]:
                        ct_text = ct.get("Text", "") or ""
                        ct_url = ct.get("FirstURL", "") or ""
                        if ct_text:
                            found_results.append({"title": ct_text[:80], "url": ct_url, "snippet": ct_text[:300]})
        except Exception:
            pass

    # ── Path 2: DuckDuckGo HTML search ─────────────────────────────────────
    if len(found_results) < max_results:
        ddg_url = f"https://html.duckduckgo.com/html/?q={encoded}"
        html = _fetch(ddg_url, timeout=10)
        if html and not _is_captcha(html):
            for m in _re.finditer(
                r'<a[^>]*class="result__a"[^>]*href="([^"]*)"[^>]*>(.*?)</a>',
                html, _re.DOTALL,
            ):
                url = m.group(1)
                title = _re.sub(r"<[^>]+>", "", m.group(2)).strip()
                snippet_m = _re.search(
                    r'<a[^>]*class="result__snippet"[^>]*>(.*?)</a>',
                    html[m.end():], _re.DOTALL,
                )
                snippet = _re.sub(r"<[^>]+>", "", snippet_m.group(1)).strip() if snippet_m else ""
                if title:
                    found_results.append({"title": title, "url": url, "snippet": snippet})
                    if len(found_results) >= max_results:
                        break

    # ── Path 3: Google fallback ────────────────────────────────────────────
    if len(found_results) < max_results:
        try:
            google_url = f"https://www.google.com/search?q={encoded}&num={max_results}"
            google_html = _fetch(google_url, timeout=8)
            if google_html and not _is_captcha(google_html):
                for m in _re.finditer(
                    r'<a[^>]*href="/url\?q=([^"&]+)[^"]*"[^>]*>(.*?)</a>',
                    google_html, _re.DOTALL,
                ):
                    url = _uparse.unquote(m.group(1))
                    title = _re.sub(r"<[^>]+>", "", m.group(2)).strip()
                    if title and url.startswith("http"):
                        # Check we don't already have this URL
                        if not any(r["url"].strip("/") == url.strip("/") for r in found_results):
                            found_results.append({"title": title, "url": url, "snippet": ""})
                            if len(found_results) >= max_results:
                                break
        except Exception:
            pass

    if not found_results:
        return (
            f"Web search is not available in this environment (DuckDuckGo is rate-limiting "
            f"programmatic requests). The model should either answer from its training data "
            f"or tell the user search is temporarily unavailable."
        )

    # ── Extract content from top result URLs ───────────────────────────────
    content_lines: list[str] = [f"Search results for: {query}\n"]

    # Show search results
    for i, r in enumerate(found_results[:max_results], 1):
        url = r.get("url", "")
        real_url = _ddg_redirect_url(url) if url and "duckduckgo.com/l/" in url else url
        snippet = r.get("snippet", "")
        content_lines.append(f"{i}. {r['title']}")
        if real_url:
            content_lines[-1] += f"\n   Source: {real_url}"
        if snippet:
            content_lines[-1] += f"\n   {snippet}"
        content_lines[-1] += "\n"

    # Fetch top 2 result pages for deeper content
    pages_fetched = 0
    for r in found_results[:min(3, max_results)]:
        url = r.get("url", "")
        if not url:
            continue
        real_url = _ddg_redirect_url(url) if "duckduckgo.com/l/" in url else url
        if not real_url.startswith("http"):
            continue

        page_html = _fetch(real_url, timeout=10)
        if not page_html or _is_captcha(page_html):
            continue

        readable = _extract_readable_text(page_html)
        if len(readable) > 200:
            pages_fetched += 1
            content_lines.append(f"\n--- Content from {real_url} ---")
            # Show first ~2000 chars of extracted content
            content_lines.append(readable[:2000])
            if len(readable) > 2000:
                content_lines.append("... (content truncated)")
            content_lines.append("")

    if pages_fetched > 0:
        content_lines.append(f"(Extracted content from {pages_fetched} page(s))")

    return "\n".join(content_lines)


@tool(description="Search memory with relevance filtering", category="knowledge")
async def search_knowledge(query: str, limit: int = 10, min_score: float = 0.0) -> str:
    """Search the knowledge base with relevance filtering.

    Searches memories and knowledge entries. Results with low relevance
    scores can be filtered out. Use for factual recall, not creative tasks.

    Args:
        query: Search query text
        limit: Maximum results to return (default 10, max 50)
        min_score: Minimum relevance score 0.0-1.0 (default 0.0 = no filter).
                   Use 0.3+ to filter out loosely related results.
    """
    limit = min(limit, 50)
    min_score = max(0.0, min(1.0, min_score))
    try:
        from backend.app.core.db import SessionLocal
        from backend.app.services.memory.manager import MemoryManager

        db = SessionLocal()
        try:
            mgr = MemoryManager(db)
            results = mgr.search(query=query, user_id=None, category=None, limit=limit * 3)
            if not results:
                return "No knowledge base entries found matching the query."

            # Filter by relevance score if feature available
            if min_score > 0.0:
                filtered = [r for r in results if r.get("score", 1.0) >= min_score]
            else:
                filtered = list(results)

            # Dedup by content hash
            seen_hashes: set[str] = set()
            deduped = []
            for r in filtered:
                content = str(r.get("content", ""))
                h = str(hash(content[:100]))
                if h not in seen_hashes:
                    seen_hashes.add(h)
                    deduped.append(r)
                    if len(deduped) >= limit:
                        break

            if not deduped:
                return f"No relevant results (score >= {min_score}). Try lowering min_score."

            parts: list[str] = [f"Knowledge base results ({len(deduped)}):"]
            for r in deduped:
                title = r.get("title", "Untitled")
                content = str(r.get("content", ""))[:250]
                category = r.get("category", "general")
                score = r.get("score", "?")
                parts.append(f"  [{category}] (score: {score}) {title}: {content}")
            return "\n".join(parts)
        finally:
            db.close()
    except ImportError:
        return "Knowledge base search is not available (MemoryManager not yet initialized)"
    except Exception as exc:
        return f"Error searching knowledge base: {exc}"


# Legacy registrations (backward compat)
register_tool("exec_command", exec_command, "Run a shell command with safety limits")
register_tool("git_log", git_log, "Show recent git commits")
register_tool("git_diff", git_diff, "Show file changes")
register_tool("web_fetch", web_fetch, "Fetch URL content")
register_tool("ask_user", ask_user, "Ask user for input")
register_tool("read_file", read_file, "Read file contents with line limit")
register_tool("write_file", write_file, "Write content to a file (requires approval)")
register_tool("list_directory", list_directory, "List directory contents")
register_tool("grep_files", grep_files, "Search for text patterns in files (like grep)")
register_tool("git_status", git_status, "Show git working tree status")
register_tool("git_show", git_show, "Show git commit details or file content from a commit")
register_tool("search_knowledge", search_knowledge, "Search knowledge base entries")
register_tool("current_datetime", current_datetime, "Get the current date and time")
register_tool("list_available_tools", list_available_tools, "List all available tools with descriptions")
register_tool("web_search", web_search, "Search the web with content extraction")
register_tool("get_repo_info", get_repo_info, "Get repository information")
register_tool("edit_file", edit_file, "Edit a file by replacing exact string")
register_tool("copy_file", copy_file, "Copy a file or directory")
register_tool("move_file", move_file, "Move or rename a file or directory")
register_tool("delete_file", delete_file, "Delete a file or empty directory")
register_tool("mkdir", mkdir, "Create a directory")
