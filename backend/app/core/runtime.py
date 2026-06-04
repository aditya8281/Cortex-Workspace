"""
CortexRuntime - OS-agnostic abstraction layer for all system operations.

Provides unified interface for:
- Filesystem operations (read, write, list, search)
- Path resolution with safety checks
- Cross-platform compatibility
- Virtual filesystem (VFS) enforcement

All system-level operations MUST go through this layer.
No direct os.* or pathlib usage allowed in business logic.
"""

import shutil
from pathlib import Path
from typing import Optional, List, Union
from abc import ABC, abstractmethod
import platform
from dataclasses import dataclass
from enum import Enum

from backend.app.core.logging import get_logger

logger = get_logger(__name__)


class OSType(Enum):
    """Supported operating systems."""
    LINUX = "linux"
    WINDOWS = "windows"
    MACOS = "macos"
    UNKNOWN = "unknown"


@dataclass
class VFSConfig:
    """Virtual filesystem safety configuration."""
    
    # System paths that are always blocked
    BLOCKED_PATHS_LINUX = {
        "/sys", "/proc", "/dev", "/run", "/boot", "/root",
        "/bin", "/sbin", "/usr", "/var", "/lib", "/lib64",
        "/etc", "/opt", "/srv", "/vm", "/mnt"
    }
    
    BLOCKED_PATHS_MACOS = {
        "/System", "/Library", "/private", "/dev", "/cores",
        "/usr/local/bin", "/usr/bin", "/bin", "/sbin", "/var"
    }
    
    BLOCKED_PATHS_WINDOWS = {
        "C:\\Windows", "C:\\System32", "C:\\Program Files",
        "C:\\Program Files (x86)", "C:\\ProgramData", "C:\\$Recycle.Bin",
        "C:\\System Volume Information"
    }
    
    # Allowed user-space directories
    ALLOWED_BASE_LINUX = ["/home", "/tmp"]
    ALLOWED_BASE_MACOS = ["/Users", "/tmp", "/var/tmp"]
    ALLOWED_BASE_WINDOWS = ["C:\\Users", "C:\\Temp"]


class OSAdapter(ABC):
    """Base adapter for OS-specific operations."""
    
    @abstractmethod
    def get_os_type(self) -> OSType:
        """Return the OS type this adapter handles."""
        pass
    
    @abstractmethod
    def get_user_workspace_root(self) -> Path:
        """Get the user's workspace root directory."""
        pass
    
    @abstractmethod
    def get_system_temp_dir(self) -> Path:
        """Get system temporary directory."""
        pass
    
    @abstractmethod
    def get_blocked_paths(self) -> set:
        """Get set of blocked system paths."""
        pass
    
    @abstractmethod
    def normalize_path(self, path: Union[str, Path]) -> Path:
        """Normalize a path in a cross-platform way."""
        pass


class LinuxAdapter(OSAdapter):
    """Adapter for Linux systems."""
    
    def get_os_type(self) -> OSType:
        return OSType.LINUX
    
    def get_user_workspace_root(self) -> Path:
        """Return user's home directory on Linux."""
        return Path.home()
    
    def get_system_temp_dir(self) -> Path:
        """Return /tmp on Linux."""
        return Path("/tmp")
    
    def get_blocked_paths(self) -> set:
        """Return Linux blocked paths."""
        return VFSConfig.BLOCKED_PATHS_LINUX.copy()
    
    def normalize_path(self, path: Union[str, Path]) -> Path:
        """Normalize path to Path object."""
        if isinstance(path, str):
            return Path(path).resolve()
        return path.resolve()


class WindowsAdapter(OSAdapter):
    """Adapter for Windows systems."""
    
    def get_os_type(self) -> OSType:
        return OSType.WINDOWS
    
    def get_user_workspace_root(self) -> Path:
        """Return user's home directory on Windows."""
        return Path.home()
    
    def get_system_temp_dir(self) -> Path:
        """Return temp directory on Windows."""
        return Path.home() / "AppData" / "Local" / "Temp"
    
    def get_blocked_paths(self) -> set:
        """Return Windows blocked paths."""
        return VFSConfig.BLOCKED_PATHS_WINDOWS.copy()
    
    def normalize_path(self, path: Union[str, Path]) -> Path:
        """Normalize path to Path object."""
        if isinstance(path, str):
            return Path(path).resolve()
        return path.resolve()


class MacOSAdapter(OSAdapter):
    """Adapter for macOS systems."""
    
    def get_os_type(self) -> OSType:
        return OSType.MACOS
    
    def get_user_workspace_root(self) -> Path:
        """Return user's home directory on macOS."""
        return Path.home()
    
    def get_system_temp_dir(self) -> Path:
        """Return temp directory on macOS."""
        return Path("/var/tmp")
    
    def get_blocked_paths(self) -> set:
        """Return macOS blocked paths."""
        return VFSConfig.BLOCKED_PATHS_MACOS.copy()
    
    def normalize_path(self, path: Union[str, Path]) -> Path:
        """Normalize path to Path object."""
        if isinstance(path, str):
            return Path(path).resolve()
        return path.resolve()


class CortexRuntime:
    """
    Main runtime abstraction layer for all system operations.
    
    Provides OS-agnostic interface for:
    - File operations (read, write, list)
    - Path resolution and validation
    - VFS safety checks
    - Cross-platform compatibility
    """
    
    _instance: Optional['CortexRuntime'] = None
    _os_adapter: Optional[OSAdapter] = None
    _workspace_root: Optional[Path] = None
    
    def __new__(cls):
        """Singleton pattern - ensure only one instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the runtime with appropriate OS adapter."""
        if self._initialized:
            return
        
        self._os_adapter = self._select_adapter()
        self._workspace_root = None  # Will be set by application
        self._initialized = True
        
        logger.info(f"CortexRuntime initialized for {self._os_adapter.get_os_type().value}")
    
    @staticmethod
    def _select_adapter() -> OSAdapter:
        """Select the appropriate adapter based on platform."""
        system = platform.system().lower()
        
        if system == "linux":
            return LinuxAdapter()
        elif system == "windows":
            return WindowsAdapter()
        elif system == "darwin":
            return MacOSAdapter()
        else:
            logger.warning(f"Unknown OS: {system}, using Linux adapter as fallback")
            return LinuxAdapter()
    
    def set_workspace_root(self, root: Union[str, Path]) -> None:
        """
        Set the Cortex workspace root directory.
        
        All file operations are relative to this root.
        Must be called during application initialization.
        """
        normalized = self._os_adapter.normalize_path(root)
        self._validate_path_safe(normalized)
        self._workspace_root = normalized
        logger.info(f"Workspace root set to: {self._workspace_root}")
    
    def get_workspace_root(self) -> Path:
        """Get the current workspace root."""
        if self._workspace_root is None:
            raise RuntimeError("Workspace root not set. Call set_workspace_root() first.")
        return self._workspace_root
    
    def get_user_workspace_root(self) -> Path:
        """Get user's home directory (OS-agnostic)."""
        return self._os_adapter.get_user_workspace_root()
    
    def get_os_type(self) -> OSType:
        """Get the detected OS type."""
        return self._os_adapter.get_os_type()
    
    def get_system_temp_dir(self) -> Path:
        """Get system temporary directory (OS-agnostic)."""
        return self._os_adapter.get_system_temp_dir()
    
    # ========== PATH VALIDATION & SAFETY ==========
    
    def _validate_path_safe(self, path: Path) -> bool:
        """
        Validate that a path is safe for operations.
        
        Checks:
        - Path is not in blocked system directories
        - Path is absolute and resolved
        - Path exists or parent exists
        
        Raises: ValueError if path is unsafe
        """
        resolved = path.resolve()
        blocked = self._os_adapter.get_blocked_paths()
        
        # Check if path is in blocked directories
        for blocked_path in blocked:
            try:
                blocked_p = Path(blocked_path).resolve()
                if resolved.is_relative_to(blocked_p):
                    raise ValueError(f"Access denied: {path} is in blocked system path: {blocked_path}")
            except (ValueError, OSError):
                # is_relative_to not available or path error - skip this check
                pass
        
        logger.debug(f"Path validated as safe: {resolved}")
        return True
    
    def _resolve_user_path(self, path: Union[str, Path]) -> Path:
        """
        Resolve a user-provided path safely.
        
        Handles:
        - Relative paths (relative to workspace root)
        - Absolute paths (must be within user space)
        - ~ expansion
        """
        if isinstance(path, str):
            # Expand ~ to home directory
            if path.startswith("~"):
                path = str(Path(path).expanduser())
            path = Path(path)
        
        # If relative, make relative to workspace root
        if not path.is_absolute():
            workspace = self.get_workspace_root()
            path = workspace / path
        
        # Resolve and validate
        resolved = path.resolve()
        self._validate_path_safe(resolved)
        return resolved
    
    # ========== FILESYSTEM OPERATIONS ==========
    
    def read_file(self, path: Union[str, Path], encoding: str = "utf-8") -> str:
        """
        Read file contents safely.
        
        Args:
            path: File path (relative or absolute)
            encoding: Text encoding (default: utf-8)
        
        Returns:
            File contents as string
        
        Raises:
            ValueError: If path is unsafe
            FileNotFoundError: If file doesn't exist
            IOError: If read fails
        """
        try:
            resolved = self._resolve_user_path(path)
            return resolved.read_text(encoding=encoding)
        except Exception as e:
            logger.error(f"Failed to read file {path}: {e}")
            raise
    
    def write_file(self, path: Union[str, Path], content: str, encoding: str = "utf-8") -> None:
        """
        Write file contents safely.
        
        Creates parent directories if needed.
        
        Args:
            path: File path (relative or absolute)
            content: Content to write
            encoding: Text encoding (default: utf-8)
        
        Raises:
            ValueError: If path is unsafe
            IOError: If write fails
        """
        try:
            resolved = self._resolve_user_path(path)
            resolved.parent.mkdir(parents=True, exist_ok=True)
            resolved.write_text(content, encoding=encoding)
            logger.debug(f"File written: {resolved}")
        except Exception as e:
            logger.error(f"Failed to write file {path}: {e}")
            raise
    
    def append_file(self, path: Union[str, Path], content: str, encoding: str = "utf-8") -> None:
        """Append content to file safely."""
        try:
            resolved = self._resolve_user_path(path)
            resolved.parent.mkdir(parents=True, exist_ok=True)
            with open(resolved, "a", encoding=encoding) as f:
                f.write(content)
            logger.debug(f"Content appended to: {resolved}")
        except Exception as e:
            logger.error(f"Failed to append to file {path}: {e}")
            raise
    
    def list_dir(self, path: Union[str, Path] = ".") -> List[Path]:
        """
        List directory contents safely.
        
        Args:
            path: Directory path (default: workspace root)
        
        Returns:
            List of Path objects for directory contents
        
        Raises:
            ValueError: If path is unsafe or not a directory
        """
        try:
            resolved = self._resolve_user_path(path)
            if not resolved.is_dir():
                raise ValueError(f"Not a directory: {path}")
            return sorted(resolved.iterdir())
        except Exception as e:
            logger.error(f"Failed to list directory {path}: {e}")
            raise
    
    def walk_dir(self, path: Union[str, Path] = ".", max_depth: int = -1) -> List[tuple]:
        """
        Walk directory tree safely.
        
        Args:
            path: Starting directory (default: workspace root)
            max_depth: Maximum recursion depth (-1 = unlimited)
        
        Yields:
            Tuples of (dirpath, dirnames, filenames)
        
        Raises:
            ValueError: If path is unsafe
        """
        try:
            resolved = self._resolve_user_path(path)
            
            def _walk(current_path: Path, depth: int):
                if max_depth >= 0 and depth > max_depth:
                    return
                
                try:
                    entries = list(current_path.iterdir())
                    dirs = [e for e in entries if e.is_dir()]
                    files = [e for e in entries if e.is_file()]
                    
                    yield (current_path, dirs, files)
                    
                    for d in dirs:
                        yield from _walk(d, depth + 1)
                except (PermissionError, OSError) as e:
                    logger.warning(f"Cannot access {current_path}: {e}")
            
            return _walk(resolved, 0)
        except Exception as e:
            logger.error(f"Failed to walk directory {path}: {e}")
            raise
    
    def file_exists(self, path: Union[str, Path]) -> bool:
        """Check if file exists safely."""
        try:
            resolved = self._resolve_user_path(path)
            return resolved.exists()
        except (ValueError, OSError):
            return False
    
    def dir_exists(self, path: Union[str, Path]) -> bool:
        """Check if directory exists safely."""
        try:
            resolved = self._resolve_user_path(path)
            return resolved.is_dir()
        except (ValueError, OSError):
            return False
    
    def create_dir(self, path: Union[str, Path]) -> None:
        """Create directory safely."""
        try:
            resolved = self._resolve_user_path(path)
            resolved.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Directory created: {resolved}")
        except Exception as e:
            logger.error(f"Failed to create directory {path}: {e}")
            raise
    
    def delete_file(self, path: Union[str, Path]) -> None:
        """Delete file safely."""
        try:
            resolved = self._resolve_user_path(path)
            resolved.unlink(missing_ok=True)
            logger.debug(f"File deleted: {resolved}")
        except Exception as e:
            logger.error(f"Failed to delete file {path}: {e}")
            raise
    
    def delete_dir(self, path: Union[str, Path], recursive: bool = True) -> None:
        """Delete directory safely."""
        try:
            resolved = self._resolve_user_path(path)
            if recursive:
                shutil.rmtree(resolved, ignore_errors=True)
            else:
                resolved.rmdir()
            logger.debug(f"Directory deleted: {resolved}")
        except Exception as e:
            logger.error(f"Failed to delete directory {path}: {e}")
            raise
    
    def copy_file(self, src: Union[str, Path], dst: Union[str, Path]) -> None:
        """Copy file safely."""
        try:
            src_resolved = self._resolve_user_path(src)
            dst_resolved = self._resolve_user_path(dst)
            dst_resolved.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_resolved, dst_resolved)
            logger.debug(f"File copied: {src_resolved} -> {dst_resolved}")
        except Exception as e:
            logger.error(f"Failed to copy file {src} to {dst}: {e}")
            raise
    
    def move_file(self, src: Union[str, Path], dst: Union[str, Path]) -> None:
        """Move file safely."""
        try:
            src_resolved = self._resolve_user_path(src)
            dst_resolved = self._resolve_user_path(dst)
            dst_resolved.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src_resolved), str(dst_resolved))
            logger.debug(f"File moved: {src_resolved} -> {dst_resolved}")
        except Exception as e:
            logger.error(f"Failed to move file {src} to {dst}: {e}")
            raise
    
    def get_file_modification_time(self, path: Union[str, Path]) -> float:
        """Get file modification time safely."""
        try:
            resolved = self._resolve_user_path(path)
            return resolved.stat().st_mtime
        except Exception as e:
            logger.error(f"Failed to get mtime for {path}: {e}")
            raise
    
    def get_file_size(self, path: Union[str, Path]) -> int:
        """Get file size in bytes safely."""
        try:
            resolved = self._resolve_user_path(path)
            return resolved.stat().st_size
        except Exception as e:
            logger.error(f"Failed to get file size for {path}: {e}")
            raise
    
    # ========== SEARCH OPERATIONS ==========
    
    def search_files(self, pattern: str, root: Union[str, Path] = ".") -> List[Path]:
        """
        Search for files matching pattern safely.
        
        Args:
            pattern: Glob pattern (e.g., "*.py", "**/*.txt")
            root: Search root directory
        
        Returns:
            List of matching Path objects
        """
        try:
            resolved = self._resolve_user_path(root)
            return list(resolved.glob(pattern))
        except Exception as e:
            logger.error(f"Failed to search files with pattern {pattern}: {e}")
            raise
    
    # ========== SINGLETON ACCESS ==========
    
    @classmethod
    def get_instance(cls) -> 'CortexRuntime':
        """Get the singleton instance."""
        if cls._instance is None:
            cls()
        return cls._instance


# Module-level convenience functions
def get_runtime() -> CortexRuntime:
    """Get the CortexRuntime singleton instance."""
    return CortexRuntime.get_instance()
