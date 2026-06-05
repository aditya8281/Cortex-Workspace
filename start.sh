#!/usr/bin/env bash

# ==============================================================================
# Cortex Workspace - Quick Startup Pipeline
# ==============================================================================
# This script automates backend and frontend setup, migrations, and starts the
# local development environment.
# ==============================================================================

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

# Ensure backend package can be imported and force PyTorch to use CPU for embeddings to save VRAM for local LLMs
export PYTHONPATH="."
export CUDA_VISIBLE_DEVICES=""
BOOTSTRAP_DIR=".cortex_bootstrap"
UV_SYNC_STAMP="$BOOTSTRAP_DIR/uv-sync.stamp"
INDEX_STAMP="$BOOTSTRAP_DIR/index.stamp"

mkdir -p "$BOOTSTRAP_DIR"

# Text format definitions
BOLD="\033[1m"
GREEN="\033[32m"
BLUE="\033[34m"
YELLOW="\033[33m"
CYAN="\033[36m"
RED="\033[31m"
RESET="\033[0m"

echo -e "${BOLD}${BLUE}========================================${RESET}"
echo -e "${BOLD}${CYAN}            CORTEX WORKSPACE            ${RESET}"
echo -e "${BOLD}${BLUE}========================================${RESET}"
echo -e "Starting local development services...\n"

# 1. Check and copy environment variables
if [ ! -f .env ]; then
    echo -e "${YELLOW}[+] .env file not found. Copying from .env.example...${RESET}"
    cp .env.example .env
    
    # Generate secure random secret key
    if command -v openssl >/dev/null 2>&1; then
        SECRET_KEY=$(openssl rand -hex 32)
    else
        SECRET_KEY="cortex_fallback_secret_$(date +%s)_$RANDOM"
    fi
    
    # Replace default placeholder key
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s/SECRET_KEY=change_this_to_a_secure_random_string/SECRET_KEY=${SECRET_KEY}/g" .env
    else
        sed -i "s/SECRET_KEY=change_this_to_a_secure_random_string/SECRET_KEY=${SECRET_KEY}/g" .env
    fi
    echo -e "${GREEN}[✓] .env file created and configured with random SECRET_KEY.${RESET}"
else
    echo -e "${GREEN}[✓] .env file verified.${RESET}"
fi

# 2. Verify backend dependencies
echo -e "\n${BOLD}${CYAN}[Phase 1/4] Checking python dependencies (uv)...${RESET}"
if command -v uv >/dev/null 2>&1; then
    if [ ! -f "$UV_SYNC_STAMP" ] || [ pyproject.toml -nt "$UV_SYNC_STAMP" ] || [ uv.lock -nt "$UV_SYNC_STAMP" ]; then
        uv sync
        touch "$UV_SYNC_STAMP"
        echo -e "${GREEN}[✓] Python dependencies verified and synchronized.${RESET}"
    else
        echo -e "${GREEN}[✓] Python dependencies already synchronized.${RESET}"
    fi
else
    echo -e "${RED}[!] 'uv' package manager not found. Please install uv or run dependencies manually.${RESET}"
    exit 1
fi

# 3. Apply database migrations
echo -e "\n${BOLD}${CYAN}[Phase 2/4] Applying database migrations...${RESET}"
uv run alembic upgrade head
echo -e "${GREEN}[✓] Database migrations applied successfully.${RESET}"

# 4. Rebuild semantic index
echo -e "\n${BOLD}${CYAN}[Phase 3/4] Rebuilding repository semantic index...${RESET}"
if [ "${SKIP_INDEX_REBUILD:-0}" = "1" ]; then
    echo -e "${YELLOW}[+] Semantic index rebuild skipped via SKIP_INDEX_REBUILD=1.${RESET}"
elif [ ! -f "$INDEX_STAMP" ] || [ backend/app -nt "$INDEX_STAMP" ] || [ frontend/app -nt "$INDEX_STAMP" ] || [ scripts/rebuild_index.py -nt "$INDEX_STAMP" ]; then
    uv run python scripts/rebuild_index.py
    touch "$INDEX_STAMP"
    echo -e "${GREEN}[✓] Semantic index populated (.cortex vector store ready).${RESET}"
else
    echo -e "${GREEN}[✓] Semantic index already up to date.${RESET}"
fi

# 5. Check and configure frontend dependencies
echo -e "\n${BOLD}${CYAN}[Phase 4/4] Setting up frontend dependencies...${RESET}"
if [ -d "frontend" ]; then
    if [ ! -d "frontend/node_modules" ] || [ ! -f "frontend/node_modules/.package-lock.json" ] || [ "frontend/package-lock.json" -nt "frontend/node_modules/.package-lock.json" ]; then
        echo -e "${YELLOW}[+] node_modules not found in frontend. Running npm install...${RESET}"
        (cd frontend && npm install --no-audit --no-fund)
        echo -e "${GREEN}[✓] Frontend dependencies installed successfully.${RESET}"
    else
        echo -e "${GREEN}[✓] Frontend node_modules verified.${RESET}"
    fi
else
    echo -e "${RED}[!] 'frontend' directory not found. Skipping frontend setup.${RESET}"
fi

# 6. Concurrently run both services
echo -e "\n${BOLD}${GREEN}====================================================${RESET}"
echo -e "${BOLD}${GREEN}  ✓ Setup complete! Launching development servers...  ${RESET}"
echo -e "${BOLD}${GREEN}====================================================${RESET}"
echo -e "${CYAN}Backend API will be live at:   ${BOLD}http://localhost:8000${RESET}"
echo -e "${CYAN}Frontend UI will be live at:    ${BOLD}http://localhost:3000${RESET}"
echo -e "Press ${BOLD}Ctrl+C${RESET} to terminate both servers concurrently.\n"

# Process cleanup handler
cleanup() {
    echo -e "\n\n${YELLOW}[+] Shutting down backend and frontend servers...${RESET}"
    # Stop background tasks
    if [ -n "${BACKEND_PID:-}" ]; then
        kill "$BACKEND_PID" 2>/dev/null || true
    fi
    if [ -n "${FRONTEND_PID:-}" ]; then
        kill "$FRONTEND_PID" 2>/dev/null || true
    fi
    echo -e "${GREEN}[✓] All servers stopped. Goodbye!${RESET}"
    exit 0
}

trap cleanup SIGINT SIGTERM EXIT

# Start backend server in the background
uv run uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Start frontend server in the background
if [ -d "frontend" ]; then
    (cd frontend && npm run dev) &
    FRONTEND_PID=$!
fi

# Wait for both processes
wait
