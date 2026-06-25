#!/usr/bin/env python3
"""Claude Code Hook: Skill discovery reminder.

Reminds Claude to check for applicable skills before implementing.
Wired into settings.local.json PreToolUse on Bash(*make*implement*).
"""

import sys


def main():
    """Print skill discovery reminder."""
    print(
        "SKILL REMINDER: Before implementing, check if an existing skill applies.\n"
        "Run: ls .claude/skills/ or check system-reminder skill list.\n"
        "Use brainstorming before design, writing-plans before implementation, TDD for code."
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
