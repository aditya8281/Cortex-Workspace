#!/bin/bash
# Feature Module Validation Script
set -e

echo "=== Feature Module Validation ==="

EXPECTED_DIRS="memory awareness conversations repositories documents search agents notifications settings system utility integration"

# Check 1: All directories exist
echo "Checking feature directories..."
for dir in $EXPECTED_DIRS; do
  if [ ! -d "src/features/$dir" ]; then
    echo "FAIL: Missing directory src/features/$dir"
    exit 1
  fi
done
echo "PASS: All feature directories exist"

# Check 2: No cross-feature imports
echo "Checking cross-feature imports..."
CROSS_IMPORTS=$(grep -rn "from '@/features/" src/features/ --include="*.ts" --include="*.tsx" 2>/dev/null | grep -v "_template" | grep -v "node_modules" || true)
if [ -n "$CROSS_IMPORTS" ]; then
  echo "FAIL: Cross-feature imports found:"
  echo "$CROSS_IMPORTS"
  exit 1
fi
echo "PASS: No cross-feature imports"

# Check 3: All index.ts files exist
echo "Checking index.ts files..."
for dir in $EXPECTED_DIRS; do
  if [ ! -f "src/features/$dir/index.ts" ] && [ ! -f "src/features/$dir/index.tsx" ]; then
    echo "FAIL: Missing index.ts in src/features/$dir"
    exit 1
  fi
done
echo "PASS: All index.ts files exist"

# Check 4: TypeScript compiles
echo "Checking TypeScript compilation..."
npx tsc --noEmit
echo "PASS: TypeScript compiles"

# Check 5: Feature registry exists
echo "Checking feature registry..."
if [ ! -f "src/features/registry.ts" ]; then
  echo "FAIL: Missing feature registry"
  exit 1
fi
echo "PASS: Feature registry exists"

# Check 6: Conventions exist
echo "Checking conventions..."
if [ ! -f "src/features/CONVENTIONS.md" ]; then
  echo "FAIL: Missing CONVENTIONS.md"
  exit 1
fi
echo "PASS: Conventions exist"

echo "=== All feature module checks passed ==="
