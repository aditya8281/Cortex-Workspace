import sys
import platform
import shutil
from pathlib import Path


class SystemScanner:
    """
    Agent for scanning system resources, diagnosing bugs/errors, and reporting project status.
    """

    def __init__(self, db_path: str = "app.db"):
        self.db_path = Path(db_path)

    def scan(self, query: str) -> str:
        """
        Diagnose the current project status and system health.
        """
        # Gather platform info
        plat_info = f"{platform.system()} {platform.release()} ({platform.machine()})"
        python_ver = sys.version.split()[0]

        # Gather workspace space info
        total, used, free = shutil.disk_usage(".")
        free_gb = free / (1024 ** 3)

        # Gather database info
        db_status = "Not Found ❌"
        db_size_kb = 0.0
        if self.db_path.exists():
            db_status = "Available ✅"
            db_size_kb = self.db_path.stat().st_size / 1024

        report = [
            "=== SystemScanner Diagnostic Report ===",
            f"- Platform OS: {plat_info}",
            f"- Python Runtime: {python_ver}",
            f"- Database Status ({self.db_path.name}): {db_status} ({db_size_kb:.1f} KB)",
            f"- Free Workspace Disk Space: {free_gb:.2f} GB",
            "",
            "--- Quality Assurance & Code Integrity ---",
        ]

        # Scan for potential common issues in the workspace
        warnings = []
        if not Path(".env").exists():
            warnings.append("⚠️ Missing .env file. Running with fallback values.")
        else:
            env_content = Path(".env").read_text(errors="ignore")
            if "change_me" in env_content or "dev_secret" in env_content:
                warnings.append("⚠️ Secret key contains insecure default values.")

        # Check for migrations status
        if Path("migrations/versions").exists():
            migration_files = list(Path("migrations/versions").glob("*.py"))
            report.append(f"- Database Migrations: {len(migration_files)} revisions found")
        else:
            warnings.append("⚠️ No database migration folder found.")

        if warnings:
            report.append("- Health Warnings:")
            report.extend([f"  {w}" for w in warnings])
        else:
            report.append("- Health Status: Perfect! No issues detected.")

        return "\n".join(report)
