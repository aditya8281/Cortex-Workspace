# cortex-repository-intelligence

Build accurate understanding of current repository state.

## When to Use

Before any command execution, planning, or analysis that requires knowing the repo state. Always invoke as the first step.

## Process

### 1. Find Repository Root

```bash
# Walk up from pwd to find CLAUDE.md marker
root=$(pwd)
while [ ! -f "$root/CLAUDE.md" ] && [ "$root" != "/" ]; do root=$(dirname "$root"); done
if [ "$root" = "/" ]; then echo "No Cortex repo root found — ensure CLAUDE.md exists"; exit 1; fi
cd "$root"
echo "Repo root: $root"
```

### 2. Git State

```bash
git status
git branch --show-current
git log --oneline -10
git stash list 2>/dev/null
```

### 3. Active Development State

```bash
cat .agents/plans/ACTIVE_VERSION.md 2>/dev/null || echo "No ACTIVE_VERSION.md"
grep -r "in_progress\|active\|complete" .agents/plans/versions/*/progress.md 2>/dev/null || true
```

### 4. Repository Structure

```bash
find . -maxdepth 3 -type d | sort | head -40
```

### 5. Test Baseline

```bash
pytest --collect-only 2>&1 | tail -3
```

## Output

Current branch, version, phase, repo structure, and test count. Repository root discovered and cwd set.

## Examples

**Invoke before any command:**
```
Invoke cortex-repository-intelligence to discover repo state.
```
