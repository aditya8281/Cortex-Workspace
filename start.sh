#!/usr/bin/env bash

# ==============================================================================
# Cortex Workspace - Quick Startup Pipeline
# ==============================================================================
# This script automates backend and frontend setup, migrations, and starts the
# local development environment.
#
# PostgreSQL is managed automatically in user-space under CortexMemory/postgres/.
# No Docker, no sudo, no manual database creation required.
# ==============================================================================

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

# Ensure backend package can be importable by Python
export PYTHONPATH="."
BOOTSTRAP_DIR=".cortex_bootstrap"
UV_SYNC_STAMP="$BOOTSTRAP_DIR/uv-sync.stamp"

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

# ── PostgreSQL Configuration ─────────────────────────────────────────────────
CORTEX_PG_PORT=5435
CORTEX_PG_DIR="$ROOT_DIR/CortexMemory/postgres"
CORTEX_PG_DATA="$CORTEX_PG_DIR/data"
CORTEX_PG_LOG="$CORTEX_PG_DIR/pg.log"
CORTEX_PG_SOCKET="$CORTEX_PG_DIR"
CORTEX_PG_USER="cortex"
CORTEX_PG_PASS="cortex"
CORTEX_PG_DB="cortex"

# ── Locate PostgreSQL Binaries ───────────────────────────────────────────────
find_pg_bin() {
    # Check standard PATH first
    if command -v pg_ctl >/dev/null 2>&1; then
        PG_BIN_DIR="$(dirname "$(command -v pg_ctl)")"
        return 0
    fi

    # Search common Debian/Ubuntu PostgreSQL installation paths
    for dir in /usr/lib/postgresql/*/bin; do
        if [ -x "$dir/pg_ctl" ] && [ -x "$dir/initdb" ]; then
            PG_BIN_DIR="$dir"
            return 0
        fi
    done

    # Search Homebrew paths (macOS)
    for dir in /opt/homebrew/opt/postgresql@*/bin /usr/local/opt/postgresql@*/bin; do
        if [ -x "$dir/pg_ctl" ] && [ -x "$dir/initdb" ]; then
            PG_BIN_DIR="$dir"
            return 0
        fi
    done

    return 1
}

# ── PostgreSQL Lifecycle ─────────────────────────────────────────────────────
ensure_postgres() {
    echo -e "\n${BOLD}${CYAN}[Phase 0/4] Setting up local PostgreSQL...${RESET}"

    if ! find_pg_bin; then
        echo -e "${RED}[!] PostgreSQL binaries not found.${RESET}"
        echo -e "${RED}    Install PostgreSQL: sudo apt install postgresql${RESET}"
        echo -e "${RED}    or: brew install postgresql@16${RESET}"
        exit 1
    fi

    echo -e "${GREEN}[✓] PostgreSQL binaries found: ${PG_BIN_DIR}${RESET}"

    mkdir -p "$CORTEX_PG_DIR"

    # Initialize data directory if it doesn't exist
    if [ ! -d "$CORTEX_PG_DATA/base" ]; then
        echo -e "${YELLOW}[+] Initializing Cortex database cluster...${RESET}"
        "$PG_BIN_DIR/initdb" \
            -D "$CORTEX_PG_DATA" \
            --username=postgres \
            --auth=trust \
            --no-instructions \
            > "$CORTEX_PG_LOG" 2>&1
        echo -e "${GREEN}[✓] Database cluster initialized.${RESET}"
    fi

    # Check if Cortex's PostgreSQL is already running on our port
    if "$PG_BIN_DIR/pg_isready" -h 127.0.0.1 -p "$CORTEX_PG_PORT" -q 2>/dev/null; then
        echo -e "${GREEN}[✓] Cortex PostgreSQL already running on port ${CORTEX_PG_PORT}.${RESET}"
    else
        echo -e "${YELLOW}[+] Starting Cortex PostgreSQL on port ${CORTEX_PG_PORT}...${RESET}"
        "$PG_BIN_DIR/pg_ctl" \
            -D "$CORTEX_PG_DATA" \
            -l "$CORTEX_PG_LOG" \
            -o "-p $CORTEX_PG_PORT -h 127.0.0.1 -k $CORTEX_PG_SOCKET" \
            start > /dev/null 2>&1

        # Wait for server to be ready (up to 10 seconds)
        for i in $(seq 1 20); do
            if "$PG_BIN_DIR/pg_isready" -h 127.0.0.1 -p "$CORTEX_PG_PORT" -q 2>/dev/null; then
                break
            fi
            sleep 0.5
        done

        if ! "$PG_BIN_DIR/pg_isready" -h 127.0.0.1 -p "$CORTEX_PG_PORT" -q 2>/dev/null; then
            echo -e "${RED}[!] Failed to start PostgreSQL. Check log: ${CORTEX_PG_LOG}${RESET}"
            cat "$CORTEX_PG_LOG" | tail -10
            exit 1
        fi
        echo -e "${GREEN}[✓] Cortex PostgreSQL started.${RESET}"
    fi

    # Create the cortex role and database if they don't exist
    _pg_psql() {
        "$PG_BIN_DIR/psql" -h 127.0.0.1 -p "$CORTEX_PG_PORT" -U postgres -d postgres "$@" 2>/dev/null
    }

    # Create role if missing
    if ! _pg_psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='${CORTEX_PG_USER}'" | grep -q 1; then
        echo -e "${YELLOW}[+] Creating database role '${CORTEX_PG_USER}'...${RESET}"
        _pg_psql -c "CREATE ROLE ${CORTEX_PG_USER} WITH LOGIN PASSWORD '${CORTEX_PG_PASS}' SUPERUSER;" > /dev/null
        echo -e "${GREEN}[✓] Role '${CORTEX_PG_USER}' created.${RESET}"
    fi

    # Create database if missing
    if ! _pg_psql -tAc "SELECT 1 FROM pg_database WHERE datname='${CORTEX_PG_DB}'" | grep -q 1; then
        echo -e "${YELLOW}[+] Creating database '${CORTEX_PG_DB}'...${RESET}"
        _pg_psql -c "CREATE DATABASE ${CORTEX_PG_DB} OWNER ${CORTEX_PG_USER};" > /dev/null
        echo -e "${GREEN}[✓] Database '${CORTEX_PG_DB}' created.${RESET}"
    fi

    echo -e "${GREEN}[✓] Local PostgreSQL ready (port ${CORTEX_PG_PORT}).${RESET}"
}

stop_postgres() {
    if [ -n "${PG_BIN_DIR:-}" ] && [ -d "$CORTEX_PG_DATA" ]; then
        echo -e "${YELLOW}[+] Stopping Cortex PostgreSQL...${RESET}"
        "$PG_BIN_DIR/pg_ctl" -D "$CORTEX_PG_DATA" stop -m fast > /dev/null 2>&1 || true
        echo -e "${GREEN}[✓] Cortex PostgreSQL stopped.${RESET}"
    fi
}


# 0. Start PostgreSQL
ensure_postgres


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


# 4. Check and configure frontend dependencies
echo -e "\n${BOLD}${CYAN}[Phase 3/4] Setting up frontend dependencies...${RESET}"
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


# 5. Launch development servers
echo -e "\n${BOLD}${GREEN}====================================================${RESET}"
echo -e "${BOLD}${GREEN}  ✓ Setup complete! Launching development servers...  ${RESET}"
echo -e "${BOLD}${GREEN}====================================================${RESET}"
echo -e "${CYAN}Backend API will be live at:   ${BOLD}http://localhost:8000${RESET}"
echo -e "${CYAN}Frontend UI will be live at:    ${BOLD}http://localhost:3000${RESET}"
echo -e "Press ${BOLD}Ctrl+C${RESET} to terminate all services.\n"

# Process cleanup handler
cleanup() {
    echo -e "\n\n${YELLOW}[+] Shutting down all Cortex services...${RESET}"
    # Stop backend and frontend
    if [ -n "${BACKEND_PID:-}" ]; then
        kill "$BACKEND_PID" 2>/dev/null || true
    fi
    if [ -n "${FRONTEND_PID:-}" ]; then
        kill "$FRONTEND_PID" 2>/dev/null || true
    fi
    # Stop PostgreSQL
    stop_postgres
    echo -e "${GREEN}[✓] All services stopped. Goodbye!${RESET}"
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

# Wait for all background processes
wait
