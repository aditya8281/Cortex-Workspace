"""cortexd CLI entrypoint — start, stop, status, logs, restart.

Usage:
    cortexd start [--daemon] [--config PATH]
    cortexd stop
    cortexd status
    cortexd logs [--tail N] [--follow]
    cortexd restart
"""

from __future__ import annotations

import asyncio
import os
import sys
import time
from pathlib import Path

import click

from backend.app.core.logging import get_logger, setup_logging
from backend.app.daemon.health import check_all
from backend.app.daemon.lifecycle import LifecycleHook, get_lifecycle
from backend.app.daemon.pid import (
    is_running,
    read_pid,
    remove_pid,
    write_pid,
)
from backend.app.daemon.signals import (
    ShutdownRequested,
    restore_signal_handlers,
    setup_signal_handlers,
    wait_for_shutdown,
)
from backend.app.daemon.sleep import SleepManager

logger = get_logger(__name__)


class CortexDaemon:
    """Manages the full daemon lifecycle."""

    def __init__(self, config_path: str | None = None) -> None:
        self._config_path = config_path
        self._sleep_manager = SleepManager()
        self._server_task: asyncio.Task | None = None

    async def start(self) -> int:
        """Start the daemon. Returns exit code."""
        setup_signal_handlers()
        version = "0.1.0"

        try:
            write_pid(version=version)
        except Exception as exc:
            click.echo(f"Error: {exc}", err=True)
            return 1

        click.echo(f"CORTEX daemon starting (PID {os.getpid()})...")

        lifecycle = get_lifecycle()

        # Register startup hooks
        lifecycle.register(
            LifecycleHook(
                name="start_uvicorn",
                callback=self._start_uvicorn,
                phase="post_start",
                order=50,
                critical=True,
            )
        )
        lifecycle.register(
            LifecycleHook(
                name="start_sleep_manager",
                callback=self._sleep_manager.start,
                phase="post_start",
                order=200,
            )
        )

        try:
            await lifecycle.run_startup()
            click.echo("CORTEX daemon started successfully")
            # Block until shutdown
            await wait_for_shutdown()
        except ShutdownRequested:
            click.echo("Shutdown requested...")
        finally:
            await self._shutdown(lifecycle)

        return 0

    async def _start_uvicorn(self) -> None:
        """Import and start uvicorn with the FastAPI app."""
        import uvicorn

        from backend.app.main import create_daemon_app

        app = create_daemon_app()
        cfg = uvicorn.Config(
            app,
            host=os.environ.get("CORTEX_HOST", "0.0.0.0"),
            port=int(os.environ.get("CORTEX_PORT", "8000")),
            log_level=os.environ.get("CORTEX_LOG_LEVEL", "info"),
            reload=False,
        )
        server = uvicorn.Server(cfg)

        self._server_task = asyncio.create_task(server.serve())

        # Wait briefly to confirm server starts
        await asyncio.sleep(0.5)
        if not server.started:
            raise RuntimeError("uvicorn failed to start")

    async def _shutdown(self, lifecycle) -> None:
        """Perform orderly shutdown."""
        click.echo("Shutting down CORTEX daemon...")

        await self._sleep_manager.stop()

        if self._server_task and not self._server_task.done():
            self._server_task.cancel()
            try:
                await self._server_task
            except asyncio.CancelledError:
                pass

        await lifecycle.run_shutdown()
        restore_signal_handlers()
        click.echo("CORTEX daemon stopped")


# ── CLI Commands ─────────────────────────────────────────────────────


@click.group()
def cli():
    """CORTEX daemon — process lifecycle management."""


def _start_daemon(daemon: bool = False, config_path: str | None = None) -> None:
    """Shared start logic for `start` and `restart` commands."""
    if is_running():
        pid_info = read_pid()
        pid = pid_info["pid"] if pid_info else "unknown"
        click.echo(
            f"CORTEX daemon is already running (PID {pid}). Use 'cortexd stop' first.",
        )
        sys.exit(1)

    if daemon:
        pid = os.fork()
        if pid > 0:
            click.echo(f"CORTEX daemon starting in background (PID {pid})")
            sys.exit(0)
        os.setsid()
        pid2 = os.fork()
        if pid2 > 0:
            sys.exit(0)

    setup_logging()

    try:
        daemon_obj = CortexDaemon(config_path=config_path)
        exit_code = asyncio.run(daemon_obj.start())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        click.echo("\nShutdown requested...")
    except Exception as exc:
        click.echo(f"Fatal error: {exc}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--daemon", is_flag=True, help="Run as background daemon")
@click.option("--config", "config_path", type=click.Path(exists=True), help="Path to config file")
def start(daemon: bool, config_path: str | None) -> None:
    """Start the CORTEX daemon."""
    _start_daemon(daemon=daemon, config_path=config_path)


@cli.command()
def stop() -> None:
    """Stop the CORTEX daemon."""
    pid_info = read_pid()
    if not pid_info:
        click.echo("CORTEX daemon is not running")
        return

    pid = pid_info["pid"]
    click.echo(f"Stopping CORTEX daemon (PID {pid})...")

    try:
        os.kill(pid, 15)  # SIGTERM
        # Wait up to 10s for graceful shutdown
        for _ in range(50):
            time.sleep(0.2)
            if not is_running():
                break
        else:
            click.echo("Daemon did not stop gracefully, sending SIGKILL...")
            try:
                os.kill(pid, 9)  # SIGKILL
            except ProcessLookupError:
                pass
        click.echo("CORTEX daemon stopped")
    except ProcessLookupError:
        # Already dead — clean up PID file
        remove_pid()
        click.echo("CORTEX daemon was already stopped (stale PID cleaned up)")
    except PermissionError:
        click.echo(f"Permission denied: cannot signal PID {pid}", err=True)
        sys.exit(1)


@cli.command()
def status() -> None:
    """Show daemon status and health."""
    pid_info = read_pid()
    if not pid_info:
        click.echo("CORTEX daemon: NOT RUNNING")
        sys.exit(1)

    alive = is_running()
    if not alive:
        click.echo("CORTEX daemon: NOT RUNNING (stale PID)")
        sys.exit(1)

    uptime = time.time() - pid_info["start_time"]
    hours, remainder = divmod(uptime, 3600)
    minutes, seconds = divmod(remainder, 60)

    click.echo("CORTEX daemon: RUNNING")
    click.echo(f"  PID:      {pid_info['pid']}")
    click.echo(f"  Version:  {pid_info.get('version', 'unknown')}")
    click.echo(f"  Uptime:   {int(hours)}h {int(minutes)}m {int(seconds)}s")
    click.echo(f"  Started:  {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(pid_info['start_time']))}")
    click.echo()

    # Run health checks
    click.echo("Health checks:")
    try:
        report = asyncio.run(check_all())
        for probe in report.probes:
            status_str = "✓" if probe.healthy else "✗"
            click.echo(f"  {status_str} {probe.name}: {probe.detail or 'unknown'}")
        click.echo()
        click.echo(f"Summary: {report.summary}")
    except Exception as exc:
        click.echo(f"  Health check failed: {exc}")


@cli.command()
@click.option("--tail", type=int, default=50, help="Number of lines to show")
@click.option("--follow", "-f", is_flag=True, help="Follow log output")
def logs(tail: int, follow: bool) -> None:
    """View daemon logs."""
    log_dir = Path(os.environ.get("CORTEX_LOG_DIR", "logs"))
    log_file = log_dir / "daemon.log"

    if not log_file.exists():
        click.echo(f"No daemon log file found at {log_file}")
        sys.exit(1)

    if follow:
        # Follow log file
        try:
            import subprocess

            subprocess.run(["tail", "-f", str(log_file)], check=True)
        except FileNotFoundError:
            click.echo("tail command not available")
            sys.exit(1)
    else:
        # Show last N lines
        try:
            import subprocess

            subprocess.run(["tail", f"-{tail}", str(log_file)], check=True)
        except FileNotFoundError:
            with open(log_file) as f:
                lines = f.readlines()
                for line in lines[-tail:]:
                    click.echo(line, nl=False)


@cli.command()
def restart() -> None:
    """Restart the CORTEX daemon."""
    stop()
    _start_daemon()


def main() -> None:
    """Entrypoint for console_scripts."""
    cli()


if __name__ == "__main__":
    main()
