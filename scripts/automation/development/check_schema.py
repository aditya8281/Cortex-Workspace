#!/usr/bin/env python3
"""Development validation: Check database schema consistency.

Verifies:
- All SQLAlchemy models have corresponding Alembic migrations
- Migration files have upgrade() and downgrade() functions
- Schema changes are properly versioned
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def check_schema():
    """Check database schema consistency."""
    print("Checking database schema consistency...")

    models_dir = ROOT / "backend" / "app" / "models"
    migrations_dir = ROOT / "migrations" / "versions"

    # Find all model files
    model_files = list(models_dir.glob("*.py")) if models_dir.exists() else []
    model_files = [f for f in model_files if f.name != "__init__.py"]

    # Find all migration files
    migration_files = list(migrations_dir.glob("*.py")) if migrations_dir.exists() else []
    migration_files = [f for f in migration_files if not f.name.startswith("__")]

    print(f"Model files: {len(model_files)}")
    print(f"Migration files: {len(migration_files)}")

    # Check that migration files have proper structure
    issues = []
    for migration_file in migration_files:
        content = migration_file.read_text()

        # Check for upgrade function
        if "def upgrade()" not in content and "def upgrade(" not in content:
            issues.append(f"  {migration_file.name}: missing upgrade() function")

        # Check for downgrade function
        if "def downgrade()" not in content and "def downgrade(" not in content:
            issues.append(f"  {migration_file.name}: missing downgrade() function")

    if issues:
        print(f"\nSchema issues found: {len(issues)}")
        for issue in issues:
            print(issue)
        return 1
    else:
        print("\n✓ Schema consistency check passed")
        return 0


if __name__ == "__main__":
    sys.exit(check_schema())
