"""Migration script: move profile photos from CortexMemory/photos/{user_id}/ to each user's registered <storage_root>/profile/.

Usage:
    python scripts/migrate_profile_photos.py

The script will:
- Scan `StorageRegistry` entries
- For each user, if a legacy avatar exists, copy it to `<storage_root>/profile/avatar.webp`
- Create a `.backup/` folder under CortexMemory/photos/ to store originals
- Print a summary at the end

Run with the project's virtualenv activated.
"""
import shutil
import sys
from pathlib import Path

from backend.app.core.system_paths import get_system_root
from backend.app.db.session import SessionLocal
from backend.app.models.storage_registry import StorageRegistry


def main():
    print("Starting profile photos migration...")
    db = SessionLocal()
    try:
        regs = db.query(StorageRegistry).all()
    except Exception as e:
        print("Failed to query StorageRegistry:", e)
        return 1

    system_root = get_system_root()
    legacy_root = system_root / "photos"
    backup_root = legacy_root / ".backup"
    backup_root.mkdir(parents=True, exist_ok=True)

    migrated = 0
    skipped = 0
    errors = 0

    for reg in regs:
        try:
            user_id = reg.user_id
            storage_root = Path(reg.storage_root).expanduser().resolve()
            profile_dir = storage_root / "profile"
            profile_dir.mkdir(parents=True, exist_ok=True)

            legacy_avatar = legacy_root / str(user_id) / "avatar.webp"
            legacy_thumb = legacy_root / str(user_id) / "avatar_thumb.webp"

            if legacy_avatar.exists():
                dest = profile_dir / "avatar.webp"
                shutil.copy2(str(legacy_avatar), str(dest))
                # Backup originals
                bak_dir = backup_root / str(user_id)
                bak_dir.mkdir(parents=True, exist_ok=True)
                shutil.move(str(legacy_avatar), str(bak_dir / "avatar.webp"))
                if legacy_thumb.exists():
                    shutil.move(str(legacy_thumb), str(bak_dir / "avatar_thumb.webp"))
                migrated += 1
                print(f"Migrated user {user_id} -> {dest}")
            else:
                skipped += 1
        except Exception as e:
            errors += 1
            print(f"Error migrating user {reg.user_id}: {e}")

    print("\nSummary:")
    print(f"  Migrated: {migrated}")
    print(f"  Skipped (no legacy avatar): {skipped}")
    print(f"  Errors: {errors}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
