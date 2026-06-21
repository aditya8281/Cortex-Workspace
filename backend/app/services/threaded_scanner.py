"""
Multi-threaded file scanner with crash isolation.
Inspired by sist2's fork-based scanner.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from multiprocessing import cpu_count
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_MAX_WORKERS = min(cpu_count() or 4, 8)
DEFAULT_TIMEOUT = 30
BATCH_SIZE = 64


@dataclass
class ParseResult:
    file_path: str
    content: str | None = None
    metadata: dict = field(default_factory=dict)
    error: str | None = None
    elapsed_ms: float = 0.0


def _run_parser_in_process(
    file_path: str,
    parser_fn: Callable[[str], Any],
) -> dict:
    """Top-level function for ProcessPoolExecutor (must be picklable)."""
    import time

    start = time.monotonic()
    try:
        result = parser_fn(file_path)
        elapsed = (time.monotonic() - start) * 1000
        return {
            "file_path": file_path,
            "content": getattr(result, "full_text", None) if result is not None else None,
            "metadata": getattr(result, "metadata", {}) if result is not None else {},
            "error": None,
            "elapsed_ms": elapsed,
        }
    except Exception as e:
        elapsed = (time.monotonic() - start) * 1000
        return {
            "file_path": file_path,
            "content": None,
            "metadata": {},
            "error": f"{type(e).__name__}: {e}",
            "elapsed_ms": elapsed,
        }


class ThreadedScanner:
    """Multi-threaded file scanner with crash isolation.

    Uses ThreadPoolExecutor for I/O-bound work (file reads, hashing)
    and ProcessPoolExecutor for CPU-bound parsing with timeout protection.
    """

    def __init__(
        self,
        max_workers: int | None = None,
        timeout: int = DEFAULT_TIMEOUT,
        batch_size: int = BATCH_SIZE,
    ):
        self.max_workers = max_workers or DEFAULT_MAX_WORKERS
        self.timeout = timeout
        self.batch_size = batch_size

    def scan_files(
        self,
        files: list[str],
        parser_fn: Callable[[str], Any],
        max_workers: int | None = None,
        timeout: int | None = None,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> dict[str, ParseResult]:
        """Process files in parallel with crash isolation.

        Args:
            files: List of file paths to process.
            parser_fn: Callable that takes a file path and returns a ParsedDocument.
            max_workers: Override thread/process count for this run.
            timeout: Per-file timeout in seconds.
            progress_callback: Called with (completed, total) after each file.

        Returns:
            Dict mapping file_path to ParseResult.
        """
        if not files:
            return {}

        workers = max_workers or self.max_workers
        per_file_timeout = timeout or self.timeout
        total = len(files)
        results: dict[str, ParseResult] = {}
        completed = 0

        # Process in batches to limit memory usage
        for batch_start in range(0, total, self.batch_size):
            batch = files[batch_start : batch_start + self.batch_size]
            batch_results = self._process_batch(batch, parser_fn, workers, per_file_timeout)
            results.update(batch_results)
            completed += len(batch)
            if progress_callback:
                progress_callback(completed, total)

        return results

    def scan_files_threaded(
        self,
        files: list[str],
        parser_fn: Callable[[str], Any],
        max_workers: int | None = None,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> dict[str, ParseResult]:
        """Thread-based scan for I/O-bound parsers.

        Uses threads instead of processes — lower overhead, no pickling required.
        Suitable when the parser mainly reads files and does lightweight processing.
        """
        if not files:
            return {}

        workers = max_workers or self.max_workers
        total = len(files)
        results: dict[str, ParseResult] = {}
        completed = 0

        for batch_start in range(0, total, self.batch_size):
            batch = files[batch_start : batch_start + self.batch_size]
            with ThreadPoolExecutor(max_workers=workers) as executor:
                future_to_path = {}
                for fpath in batch:
                    future = executor.submit(self._safe_parse_thread, fpath, parser_fn)
                    future_to_path[future] = fpath

                for future in as_completed(future_to_path):
                    fpath = future_to_path[future]
                    try:
                        result = future.result()
                        results[fpath] = result
                    except Exception as e:
                        results[fpath] = ParseResult(
                            file_path=fpath,
                            error=f"{type(e).__name__}: {e}",
                        )

            completed += len(batch)
            if progress_callback:
                progress_callback(completed, total)

        return results

    def _process_batch(
        self,
        batch: list[str],
        parser_fn: Callable[[str], Any],
        workers: int,
        timeout: int,
    ) -> dict[str, ParseResult]:
        """Process a single batch using ProcessPoolExecutor."""
        results: dict[str, ParseResult] = {}

        with ProcessPoolExecutor(max_workers=workers) as executor:
            future_to_path = {}
            for fpath in batch:
                future = executor.submit(_run_parser_in_process, fpath, parser_fn)
                future_to_path[future] = fpath

            for future in as_completed(future_to_path):
                fpath = future_to_path[future]
                try:
                    raw = future.result(timeout=timeout)
                    results[fpath] = ParseResult(
                        file_path=raw["file_path"],
                        content=raw["content"],
                        metadata=raw["metadata"],
                        error=raw["error"],
                        elapsed_ms=raw["elapsed_ms"],
                    )
                except TimeoutError:
                    results[fpath] = ParseResult(
                        file_path=fpath,
                        error=f"Timeout after {timeout}s",
                    )
                except Exception as e:
                    results[fpath] = ParseResult(
                        file_path=fpath,
                        error=f"{type(e).__name__}: {e}",
                    )

        return results

    @staticmethod
    def _safe_parse_thread(
        file_path: str,
        parser_fn: Callable[[str], Any],
    ) -> ParseResult:
        """Execute parser in current thread with error isolation."""
        import time

        start = time.monotonic()
        try:
            result = parser_fn(file_path)
            elapsed = (time.monotonic() - start) * 1000
            return ParseResult(
                file_path=file_path,
                content=getattr(result, "full_text", None) if result is not None else None,
                metadata=getattr(result, "metadata", {}) if result is not None else {},
                elapsed_ms=elapsed,
            )
        except Exception as e:
            elapsed = (time.monotonic() - start) * 1000
            return ParseResult(
                file_path=file_path,
                error=f"{type(e).__name__}: {e}",
                elapsed_ms=elapsed,
            )


def get_threaded_scanner(
    max_workers: int | None = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> ThreadedScanner:
    """Factory for creating a ThreadedScanner with sensible defaults."""
    return ThreadedScanner(max_workers=max_workers, timeout=timeout)
