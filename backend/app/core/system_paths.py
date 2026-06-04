"""
System paths constants and configurations.

Centralized definitions for:
- Blocked system paths
- Protected directories
- VFS safety rules
- Cross-platform path handling

NO hardcoded paths should exist in business logic.
All path references must use constants from this module.
"""

# ========== LINUX BLOCKED PATHS ==========
LINUX_BLOCKED_SYSTEM_PATHS = {
    "/sys",
    "/proc",
    "/dev",
    "/run",
    "/boot",
    "/root",
    "/bin",
    "/sbin",
    "/usr",
    "/var",
    "/lib",
    "/lib64",
    "/etc",
    "/opt",
    "/srv",
    "/vm",
    "/mnt",
}

LINUX_IGNORED_DIRS = {
    "__pycache__",
    ".venv",
    "venv",
    ".cortex",
    ".pytest_cache",
    "node_modules",
    ".git",
    ".env",
}

# ========== MACOS BLOCKED PATHS ==========
MACOS_BLOCKED_SYSTEM_PATHS = {
    "/System",
    "/Library",
    "/private",
    "/dev",
    "/cores",
    "/usr/local/bin",
    "/usr/bin",
    "/bin",
    "/sbin",
    "/var",
}

MACOS_IGNORED_DIRS = {
    "__pycache__",
    ".venv",
    "venv",
    ".cortex",
    ".pytest_cache",
    "node_modules",
    ".git",
    ".env",
    ".DS_Store",
}

# ========== WINDOWS BLOCKED PATHS ==========
WINDOWS_BLOCKED_SYSTEM_PATHS = {
    "C:\\Windows",
    "C:\\System32",
    "C:\\Program Files",
    "C:\\Program Files (x86)",
    "C:\\ProgramData",
    "C:\\$Recycle.Bin",
    "C:\\System Volume Information",
}

WINDOWS_IGNORED_DIRS = {
    "__pycache__",
    ".venv",
    "venv",
    ".cortex",
    ".pytest_cache",
    "node_modules",
    ".git",
    ".env",
}

# ========== CROSS-PLATFORM SETTINGS ==========

# Directory names that should be excluded during scanning
COMMON_IGNORED_DIRS = {
    "__pycache__",
    ".venv",
    "venv",
    "env",
    ".env",
    ".cortex",
    ".pytest_cache",
    "node_modules",
    ".git",
    ".gitignore",
    ".github",
    "dist",
    "build",
    "*.egg-info",
    ".mypy_cache",
    ".tox",
    "htmlcov",
    ".coverage",
    ".idea",
    ".vscode",
}

# File extensions to exclude
IGNORED_EXTENSIONS = {
    ".pyc",
    ".pyo",
    ".pyd",
    ".so",
    ".o",
    ".a",
    ".lib",
    ".dll",
    ".exe",
    ".bin",
    ".iso",
    ".dmg",
    ".zip",
    ".tar",
    ".gz",
    ".rar",
    ".7z",
    ".bak",
    ".tmp",
    ".log",
    ".lock",
    ".cache",
}

# Maximum file size to scan (1 GB)
MAX_FILE_SIZE_BYTES = 1024 * 1024 * 1024

# Maximum total size for scanning (100 GB)
MAX_TOTAL_SCAN_SIZE_BYTES = 100 * 1024 * 1024 * 1024


def should_ignore_path(path_name: str) -> bool:
    """
    Check if a path should be ignored during scanning.
    
    Args:
        path_name: Path name to check
    
    Returns:
        True if path should be ignored
    """
    path_lower = path_name.lower()
    
    # Check if matches ignored directory names
    if path_name in COMMON_IGNORED_DIRS:
        return True
    
    # Check if matches ignored extensions
    for ext in IGNORED_EXTENSIONS:
        if path_lower.endswith(ext):
            return True
    
    return False
