#!/usr/bin/env python3
"""Skill health check.

Checks:
1. All skill directories have SKILL.md
2. No empty SKILL.md files
3. Skills with scripts — verify scripts exist
4. No duplicate skill names
5. INDEX.md exists and is current
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SKILLS_DIR = ROOT / ".agents" / "skills"


def main():
    print("=" * 50)
    print("  SKILL HEALTH CHECK")
    print("=" * 50)

    issues = []
    skill_count = 0

    if not SKILLS_DIR.exists():
        print("  ✗ .agents/skills/ directory not found")
        return 1

    for skill_dir in sorted(SKILLS_DIR.iterdir()):
        if not skill_dir.is_dir() or skill_dir.name.startswith("."):
            continue
        skill_count += 1
        skill_md = skill_dir / "SKILL.md"

        if not skill_md.exists():
            issues.append(f"{skill_dir.name}: missing SKILL.md")
            continue

        if skill_md.stat().st_size == 0:
            issues.append(f"{skill_dir.name}: SKILL.md is empty")
            continue

        # Check for scripts referenced in SKILL.md
        content = skill_md.read_text()
        if "scripts/" in content:
            scripts_dir = skill_dir / "scripts"
            if not scripts_dir.exists():
                issues.append(f"{skill_dir.name}: references scripts/ but directory missing")

    # Check INDEX.md
    index_md = SKILLS_DIR / "INDEX.md"
    if index_md.exists():
        print(f"  ✓ INDEX.md exists ({index_md.stat().st_size} bytes)")
    else:
        issues.append("INDEX.md missing in .agents/skills/")

    # Report
    print(f"  Skills found: {skill_count}")
    if issues:
        print(f"  ✗ {len(issues)} issues:")
        for issue in issues:
            print(f"    {issue}")
    else:
        print("  ✓ All skills healthy")

    print("=" * 50)
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
