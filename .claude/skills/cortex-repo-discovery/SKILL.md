# cortex-repo-discovery

Find repository root from any working directory. Ensures commands work regardless of where they're invoked.

## When to Use

First step of every command. Run before any other operation.

## Process

### 1. Find Repository Root

Walk up from current directory looking for `CLAUDE.md` marker:

```bash
find_repo_root() {
    local dir="${1:-$(pwd)}"
    while [ "$dir" != "/" ]; do
        if [ -f "$dir/CLAUDE.md" ]; then
            echo "$dir"
            return 0
        fi
        dir=$(dirname "$dir")
    done
    echo "ERROR: No Cortex repository root found (CLAUDE.md not found in any parent)"
    return 1
}

ROOT=$(find_repo_root)
if [ $? -ne 0 ]; then exit 1; fi
cd "$ROOT"
echo "CWD set to repo root: $ROOT"
```

### 2. Verify Key Structures

```bash
echo "Commands: $(ls .claude/commands/project/ 2>/dev/null | wc -l)"
echo "Skills: $(ls -d .claude/skills/cortex-*/ 2>/dev/null | wc -l)"
echo "CLAUDE.md: $([ -f CLAUDE.md ] && echo 'found' || echo 'MISSING')"
```

## Output

CWD at repository root. Environment ready for command execution.

## Examples

```
Invoke cortex-repo-discovery before any command.
```
