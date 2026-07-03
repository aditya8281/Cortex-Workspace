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
_ensure_within_workspace = ensure_within_workspace
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

    try:
        import re

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


@tool(description="Search knowledge base entries", category="knowledge")
async def search_knowledge(query: str, limit: int = 10) -> str:
    """Search the knowledge base for entries matching the query.

    Args:
        query: Search query text
        limit: Maximum results to return (default 10, max 50)
    """
    limit = min(limit, 50)
    try:
        # MemoryManager requires a db session. We create one lazily.
        from backend.app.core.db import SessionLocal
        from backend.app.services.memory.manager import MemoryManager

        db = SessionLocal()
        try:
            mgr = MemoryManager(db)
            results = mgr.search(query=query, user_id=None, category=None, limit=limit)
            if not results:
                return "No knowledge base entries found matching the query."
            parts: list[str] = [f"Knowledge base results ({len(results)}):"]
            for r in results:
                title = r.get("title", "Untitled")
                content = str(r.get("content", ""))[:200]
                category = r.get("category", "general")
                parts.append(f"  [{category}] {title}: {content}")
            return wrap_external_content("\n".join(parts), source="search:knowledge")
        finally:
            db.close()
    except ImportError:
        return "Knowledge base search is not available (MemoryManager not yet initialized)"
    except Exception as exc:
        return f"Error searching knowledge base: {exc}"


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


@tool(
    description="Search the web. Fallback to instant answers when blocked.",
    category="web",
)
async def web_search(query: str, max_results: int = 5) -> str:
    """Search the web and return results with titles and URLs.

    Tries multiple backends:
    1. DuckDuckGo Instant Answer API (zero-click, no CAPTCHA)
    2. DuckDuckGo HTML search (full results, may hit CAPTCHA)
    3. Falls back to informative error if all blocked.

    Args:
        query: The search query
        max_results: Maximum number of results to return (default 5)
    """
    import json as _json
    import re as _re
    import urllib.parse as _uparse
    import urllib.request as _ureq

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
        return bool(
            _re.search(r"anomaly-modal|challenge|captcha|unfortunately.*bot", html, _re.I)
        )

    def _ddg_redirect_url(ddg_url: str) -> str:
        """Decode a DuckDuckGo redirect URL to the actual destination."""
        # DDG redirects look like: //duckduckgo.com/l/?uddg=ENCODED_URL&rut=...
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

    # ── Path 1: DuckDuckGo Instant Answer API (no CAPTCHA, zero-click) ──
    encoded = _uparse.quote_plus(query)
    ddg_api_url = f"https://api.duckduckgo.com/?q={encoded}&format=json&no_html=1"
    api_html = _fetch(ddg_api_url)
    if api_html:
        try:
            data = _json.loads(api_html)
            abstract = data.get("Abstract", "") or ""
            answer = data.get("Answer", "") or ""
            heading = data.get("Heading", "") or ""
            results: list[dict[str, str]] = []

            # Instant Answer
            if answer:
                results.append({"title": heading or "Answer", "url": "", "snippet": answer})

            # Abstract
            if abstract and not answer:
                url = data.get("AbstractURL", "") or ""
                results.append({"title": heading or "Result", "url": url, "snippet": abstract[:500]})

            # RelatedTopics
            for topic in data.get("RelatedTopics", []):
                if isinstance(topic, dict):
                    text = topic.get("Text", "") or ""
                    t_url = topic.get("FirstURL", "") or ""
                    if text:
                        results.append({"title": text[:80], "url": t_url, "snippet": text[:300]})
                    child_topics = topic.get("Topics", [])
                    for ct in child_topics[:3]:
                        ct_text = ct.get("Text", "") or ""
                        ct_url = ct.get("FirstURL", "") or ""
                        if ct_text:
                            results.append({"title": ct_text[:80], "url": ct_url, "snippet": ct_text[:300]})

            if results:
                lines = [f"Search results for: {query}\n"]
                for i, r in enumerate(results[:max_results], 1):
                    title = r.get("title", "")
                    url = r.get("url", "")
                    snippet = r.get("snippet", "")
                    lines.append(f"{i}. {title}")
                    if url:
                        lines[-1] += f"\n   {url}"
                    if snippet:
                        lines[-1] += f"\n   {snippet}"
                    lines[-1] += "\n"
                return "\n".join(lines)
        except Exception:
            pass

    # ── Path 2: DuckDuckGo HTML search ────────────────────────────────
    ddg_url = f"https://html.duckduckgo.com/html/?q={encoded}"
    html = _fetch(ddg_url, timeout=10)
    if html:
        if _is_captcha(html):
            # Blocked — return what we have from API or give useful fallback
            pass
        else:
            # Parse simple <a> tags with results
            result_list: list[dict[str, str]] = []
            # Find result links — DuckDuckGo wraps results in <a class="result__a">
            for m in _re.finditer(
                r'<a[^>]*class="result__a"[^>]*href="([^"]*)"[^>]*>(.*?)</a>',
                html,
                _re.DOTALL,
            ):
                url = m.group(1)
                title = _re.sub(r"<[^>]+>", "", m.group(2)).strip()
                # Find following snippet
                snippet_search = _re.search(
                    r'<a[^>]*class="result__snippet"[^>]*>(.*?)</a>',
                    html[m.end():],
                    _re.DOTALL,
                )
                snippet = _re.sub(r"<[^>]+>", "", snippet_search.group(1)).strip() if snippet_search else ""
                if title:
                    result_list.append({"title": title, "url": url, "snippet": snippet})
                    if len(result_list) >= max_results:
                        break

            if result_list:
                lines = [f"Search results for: {query}\n"]
                for i, r in enumerate(result_list, 1):
                    real_url = _ddg_redirect_url(r['url'])
                    lines.append(f"{i}. {r['title']}\n   {real_url}\n   {r['snippet']}\n")
                return "\n".join(lines)

    # ── Path 3: Try Google scraping as last resort ─────────────────────
    try:
        google_url = f"https://www.google.com/search?q={encoded}&num={max_results}"
        google_html = _fetch(google_url, timeout=8)
        if google_html and not _is_captcha(google_html):
            glist: list[dict[str, str]] = []
            for m in _re.finditer(
                r'<a[^>]*href="/url\?q=([^"&]+)[^"]*"[^>]*>(.*?)</a>',
                google_html,
                _re.DOTALL,
            ):
                url = _uparse.unquote(m.group(1))
                title = _re.sub(r"<[^>]+>", "", m.group(2)).strip()
                if title and url.startswith("http"):
                    glist.append({"title": title, "url": url, "snippet": ""})
                    if len(glist) >= max_results:
                        break
            if glist:
                lines = [f"Search results for: {query}\n"]
                for i, r in enumerate(glist, 1):
                    lines.append(f"{i}. {r['title']}\n   {r['url']}\n")
                return "\n".join(lines)
    except Exception:
        pass

    # ── Fallback: use cached / pre-structured search data ──────────────
    return (
        f"Web search is not available in this environment (DuckDuckGo is rate-limiting "
        f"programmatic requests). The model should either answer from its training data "
        f"or tell the user search is temporarily unavailable."
    )


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
register_tool("web_search", web_search, "Search the web using DuckDuckGo")
register_tool("get_repo_info", get_repo_info, "Get repository information")
