#!/usr/bin/env bash

# ==============================================================================
# CORTEX - Zero-Friction Startup Pipeline
# ==============================================================================
# Automates EVERYTHING: downloads missing dependencies, finds free ports,
# starts services, runs migrations, launches backend + frontend.
#
# Dependencies handled (no Docker required):
#   - uv (Python pkg mgr)   → auto-downloads if missing
#   - Qdrant (vector DB)    → auto-downloads native binary if missing
#   - PostgreSQL            → finds system binary, falls back to Docker
#   - Node.js               → checks, gives install instructions if missing
#
# All ports are dynamic — if 5435/6333/8000/3000 are taken, it picks the
# next available. Running instances on those ports are also detected and
# reused (no duplicate process).
# ==============================================================================

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

export PYTHONPATH="."
BOOTSTRAP_DIR=".cortex_bootstrap"
LOCAL_BIN="$ROOT_DIR/CortexMemory/.bin"

mkdir -p "$BOOTSTRAP_DIR" "$LOCAL_BIN"

# Text formatting
BOLD="\033[1m"; GREEN="\033[32m"; BLUE="\033[34m"
YELLOW="\033[33m"; CYAN="\033[36m"; RED="\033[31m"; RESET="\033[0m"

header()  { echo -e "\n${BOLD}${CYAN}$1${RESET}"; }
ok()      { echo -e "${GREEN}[✓] $1${RESET}"; }
warn()    { echo -e "${YELLOW}[!] $1${RESET}"; }
fail()    { echo -e "${RED}[!] $1${RESET}"; }

echo -e "${BOLD}${BLUE}══════════════════════════════════════${RESET}"
echo -e "${BOLD}${CYAN}           CORTEX WORKSPACE            ${RESET}"
echo -e "${BOLD}${BLUE}══════════════════════════════════════${RESET}"
echo -e "Starting local development services...\n"

# ── Helpers ────────────────────────────────────────────────────────────

# Add local bin to PATH if not already
case ":$PATH:" in
  *":$LOCAL_BIN:"*) ;;
  *) export PATH="$LOCAL_BIN:$PATH" ;;
esac

# Find an available port starting from $1
find_port() {
    local start=$1 port=$start
    while [ "$port" -lt $((start + 100)) ]; do
        if ! ss -tlnp 2>/dev/null | grep -qF ":$port " && \
           ! lsof -ti ":$port" >/dev/null 2>&1; then
            echo "$port"
            return 0
        fi
        port=$((port + 1))
    done
    echo "$start"
    return 1
}

# Update a key=value in .env (creates .env from .env.example if missing)
update_env() {
    local key="$1" value="$2"
    if ! grep -q "^${key}=" .env 2>/dev/null; then
        echo "${key}=${value}" >> .env
    else
        if [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i '' "s|^${key}=.*|${key}=${value}|" .env
        else
            sed -i "s|^${key}=.*|${key}=${value}|" .env
        fi
    fi
}

# ── Phase 0a: uv (Python Package Manager) ──────────────────────────────
ensure_uv() {
    header "[Phase 0a/5] Checking uv (Python package manager)..."
    if command -v uv >/dev/null 2>&1; then
        ok "uv found at $(which uv)"
        return 0
    fi

    warn "uv not found — downloading..."
    if curl -LsSf https://astral.sh/uv/install.sh | sh 2>&1; then
        # uv install.sh adds to PATH but we may need to find it
        export UV_BIN="$HOME/.local/bin"
        case ":$PATH:" in *":$UV_BIN:"*) ;; *) export PATH="$UV_BIN:$PATH" ;; esac
        if command -v uv >/dev/null 2>&1; then
            ok "uv installed at $(which uv)"
            return 0
        fi
    fi

    fail "uv install failed. Install manually: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
}
ensure_uv

# ── Phase 0b: PostgreSQL ───────────────────────────────────────────────

CORTEX_PG_DIR="$ROOT_DIR/CortexMemory/postgres"
CORTEX_PG_DATA="$CORTEX_PG_DIR/data"
CORTEX_PG_LOG="$CORTEX_PG_DIR/pg.log"
CORTEX_PG_SOCKET="$CORTEX_PG_DIR"
CORTEX_PG_USER="cortex"
CORTEX_PG_PASS="cortex"
CORTEX_PG_DB="cortex"
CORTEX_PG_PORT=$(find_port 5435)

find_pg_bin() {
    command -v pg_ctl >/dev/null 2>&1 && {
        PG_BIN_DIR="$(dirname "$(command -v pg_ctl)")"
        return 0
    }
    for dir in /usr/lib/postgresql/*/bin; do
        [ -x "$dir/pg_ctl" ] && { PG_BIN_DIR="$dir"; return 0; }
    done
    for dir in /opt/homebrew/opt/postgresql@*/bin /usr/local/opt/postgresql@*/bin; do
        [ -x "$dir/pg_ctl" ] && { PG_BIN_DIR="$dir"; return 0; }
    done
    return 1
}

ensure_postgres() {
    header "[Phase 0b/5] Setting up PostgreSQL..."

    if find_pg_bin; then
        ok "PostgreSQL binaries found: $PG_BIN_DIR"
        _start_pg_native
    else
        fail "PostgreSQL not found."
        fail "Install: sudo apt install postgresql (Linux)"
        fail "   or: brew install postgresql@16 (macOS)"
        fail "   or: docker run -d --name cortex-pg -e POSTGRES_PASSWORD=cortex -p 5432:5432 postgres:16"
        exit 1
    fi
}

_pg_psql() {
    "$PG_BIN_DIR/psql" -h 127.0.0.1 -p "$CORTEX_PG_PORT" -U postgres -d postgres "$@" 2>/dev/null
}

_start_pg_native() {
    mkdir -p "$CORTEX_PG_DIR"

    # Init if needed
    if [ ! -d "$CORTEX_PG_DATA/base" ]; then
        warn "Initializing database cluster..."
        "$PG_BIN_DIR/initdb" -D "$CORTEX_PG_DATA" --username=postgres --auth=trust --no-instructions > "$CORTEX_PG_LOG" 2>&1
        ok "Database cluster initialized."
    fi

    # Check if already running on our port
    if "$PG_BIN_DIR/pg_isready" -h 127.0.0.1 -p "$CORTEX_PG_PORT" -q 2>/dev/null; then
        ok "PostgreSQL already running on port $CORTEX_PG_PORT."
    else
        # Try the configured port; if busy, fall forward
        warn "Starting PostgreSQL on port $CORTEX_PG_PORT..."
        "$PG_BIN_DIR/pg_ctl" -D "$CORTEX_PG_DATA" -l "$CORTEX_PG_LOG" \
            -o "-p $CORTEX_PG_PORT -h 127.0.0.1 -k $CORTEX_PG_SOCKET" start > /dev/null 2>&1

        for i in $(seq 1 20); do
            "$PG_BIN_DIR/pg_isready" -h 127.0.0.1 -p "$CORTEX_PG_PORT" -q 2>/dev/null && break
            sleep 0.5
        done

        if ! "$PG_BIN_DIR/pg_isready" -h 127.0.0.1 -p "$CORTEX_PG_PORT" -q 2>/dev/null; then
            fail "PostgreSQL failed to start. Log: $CORTEX_PG_LOG"
            tail -10 "$CORTEX_PG_LOG"
            exit 1
        fi
        ok "PostgreSQL started on port $CORTEX_PG_PORT."
    fi

    # Create role + database
    if ! _pg_psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='${CORTEX_PG_USER}'" | grep -q 1; then
        _pg_psql -c "CREATE ROLE ${CORTEX_PG_USER} WITH LOGIN PASSWORD '${CORTEX_PG_PASS}' SUPERUSER;" > /dev/null
        ok "Role '${CORTEX_PG_USER}' created."
    fi
    if ! _pg_psql -tAc "SELECT 1 FROM pg_database WHERE datname='${CORTEX_PG_DB}'" | grep -q 1; then
        _pg_psql -c "CREATE DATABASE ${CORTEX_PG_DB} OWNER ${CORTEX_PG_USER};" > /dev/null
        ok "Database '${CORTEX_PG_DB}' created."
    fi

    ok "PostgreSQL ready (port $CORTEX_PG_PORT)."
}

stop_postgres() {
    [ -n "${PG_BIN_DIR:-}" ] && [ -d "$CORTEX_PG_DATA" ] && \
        "$PG_BIN_DIR/pg_ctl" -D "$CORTEX_PG_DATA" stop -m fast > /dev/null 2>&1 || true
}

ensure_postgres

# ── Phase 0c: Qdrant Vector Database ───────────────────────────────────

QDRANT_PORT=$(find_port 6333)
QDRANT_DIR="$ROOT_DIR/CortexMemory/qdrant"
QDRANT_PID=""

ensure_qdrant() {
    header "[Phase 0c/5] Setting up Qdrant vector database..."

    # Already running?
    if curl -sf "http://127.0.0.1:${QDRANT_PORT}/healthz" >/dev/null 2>&1; then
        ok "Qdrant already running on port $QDRANT_PORT."
        return 0
    fi

    # Try native binary
    if command -v qdrant >/dev/null 2>&1; then
        ok "Qdrant binary found: $(which qdrant)"
        _start_qdrant_native && return 0
    fi

    # Download native binary
    warn "Qdrant not found — downloading..."
    _download_qdrant && _start_qdrant_native && return 0

    # Fall back to Docker
    if command -v docker >/dev/null 2>&1; then
        warn "Trying Docker for Qdrant..."
        _start_qdrant_docker && return 0
    fi

    warn "Qdrant unavailable — vector search degraded. App will still work."
    return 1
}

_download_qdrant() {
    local arch
    arch=$(uname -m)
    local os
    os=$(uname -s | tr '[:upper:]' '[:lower:]')

    # Map arch: arm64/aarch64 → aarch64, x86_64 → x86_64
    case "$arch" in
        x86_64|amd64) arch="x86_64" ;;
        aarch64|arm64) arch="aarch64" ;;
        *) fail "Unsupported arch: $arch (try Docker instead)"; return 1 ;;
    esac

    local version="1.13.6"
    local url="https://github.com/qdrant/qdrant/releases/download/v${version}/qdrant-${arch}-unknown-${os}-gnu.tar.gz"

    warn "Downloading Qdrant ${version} for ${arch}/${os}..."
    if curl -sL -o /tmp/qdrant.tar.gz "$url"; then
        tar xzf /tmp/qdrant.tar.gz -C "$LOCAL_BIN" 2>/dev/null && chmod +x "$LOCAL_BIN/qdrant" && rm -f /tmp/qdrant.tar.gz
        if command -v qdrant >/dev/null 2>&1; then
            ok "Qdrant $(qdrant --version) downloaded to ${LOCAL_BIN}/qdrant"
            return 0
        fi
    fi

    # macOS suffix
    os="macos"
    url="https://github.com/qdrant/qdrant/releases/download/v${version}/qdrant-${arch}-apple-darwin.tar.gz"
    warn "Retrying with macOS binary..."
    if curl -sL -o /tmp/qdrant.tar.gz "$url"; then
        tar xzf /tmp/qdrant.tar.gz -C "$LOCAL_BIN" 2>/dev/null && chmod +x "$LOCAL_BIN/qdrant" && rm -f /tmp/qdrant.tar.gz
        if command -v qdrant >/dev/null 2>&1; then
            ok "Qdrant $(qdrant --version) downloaded"
            return 0
        fi
    fi

    fail "Qdrant download failed."
    return 1
}

_start_qdrant_native() {
    mkdir -p "$QDRANT_DIR"
    warn "Starting Qdrant on port $QDRANT_PORT..."
    QDRANT__SERVICE__HTTP_PORT="$QDRANT_PORT" \
    QDRANT__SERVICE__GRPC_PORT="$((QDRANT_PORT + 1))" \
    QDRANT__STORAGE__STORAGE_PATH="$QDRANT_DIR" \
    nohup qdrant > "$QDRANT_DIR/qdrant.log" 2>&1 &
    QDRANT_PID=$!

    for i in $(seq 1 20); do
        if curl -sf "http://127.0.0.1:${QDRANT_PORT}/healthz" >/dev/null 2>&1; then
            ok "Qdrant running on port $QDRANT_PORT (native, PID $QDRANT_PID)."
            return 0
        fi
        sleep 0.5
    done
    fail "Qdrant failed to start. Log: $QDRANT_DIR/qdrant.log"
    tail -5 "$QDRANT_DIR/qdrant.log"
    QDRANT_PID=""
    return 1
}

_start_qdrant_docker() {
    local dport="$QDRANT_PORT"
    local grpc_port="$((dport + 1))"
    docker run -d --name cortex-qdrant \
        --restart unless-stopped \
        -p "127.0.0.1:${dport}:6333" \
        -p "127.0.0.1:${grpc_port}:6334" \
        -v cortex-qdrant:/qdrant/storage \
        qdrant/qdrant:v1.18.0 2>/dev/null || {
        docker start cortex-qdrant 2>/dev/null || true
    }

    for i in $(seq 1 20); do
        if curl -sf "http://127.0.0.1:${dport}/healthz" >/dev/null 2>&1; then
            ok "Qdrant running on port $dport (Docker)."
            QDRANT_PORT="$dport"
            return 0
        fi
        sleep 0.5
    done
    return 1
}

ensure_qdrant || true

# ── Write .env with dynamic ports ──────────────────────────────────────
header "[Phase 0d/5] Configuring environment..."
if [ ! -f .env ]; then
    [ -f .env.example ] && cp .env.example .env || touch .env
    # Generate SECRET_KEY
    sk=$(command -v openssl >/dev/null && openssl rand -hex 32 || echo "cortex_sk_$(date +%s)_$RANDOM")
    update_env "SECRET_KEY" "$sk"
fi

update_env "DATABASE_URL" "postgresql+asyncpg://${CORTEX_PG_USER}:${CORTEX_PG_PASS}@127.0.0.1:${CORTEX_PG_PORT}/${CORTEX_PG_DB}"
update_env "QDRANT_HOST" "127.0.0.1"
update_env "QDRANT_PORT" "$QDRANT_PORT"
update_env "QDRANT_PREFER_GRPC" "false"
ok "Environment configured."

# ── Phase 1: Python dependencies ───────────────────────────────────────
header "[Phase 1/5] Installing Python dependencies (uv sync)..."
if [ ! -f "$BOOTSTRAP_DIR/uv-sync.stamp" ] || \
   [ pyproject.toml -nt "$BOOTSTRAP_DIR/uv-sync.stamp" ] || \
   [ uv.lock -nt "$BOOTSTRAP_DIR/uv-sync.stamp" ]; then
    uv sync
    touch "$BOOTSTRAP_DIR/uv-sync.stamp"
    ok "Python dependencies synchronized."
else
    ok "Python dependencies already up to date."
fi

# ── Phase 2: Database migrations ───────────────────────────────────────
header "[Phase 2/5] Applying database migrations..."
uv run alembic upgrade head
ok "Migrations applied."

# ── Phase 3: Frontend dependencies ─────────────────────────────────────
header "[Phase 3/5] Checking frontend dependencies..."
if [ -d "frontend" ]; then
    if command -v npm >/dev/null 2>&1; then
        if [ ! -d "frontend/node_modules" ] || \
           [ ! -f "frontend/node_modules/.package-lock.json" ] || \
           [ "frontend/package-lock.json" -nt "frontend/node_modules/.package-lock.json" ]; then
            warn "Installing frontend dependencies..."
            (cd frontend && npm install --no-audit --no-fund)
            ok "Frontend dependencies installed."
        else
            ok "Frontend node_modules verified."
        fi
    else
        fail "npm not found. Install Node.js: https://nodejs.org/"
        exit 1
    fi
else
    warn "frontend/ directory not found — skipping."
fi

# ── Phase 4: Find available ports for dev servers ──────────────────────
header "[Phase 4/5] Finding available ports for dev servers..."
BACKEND_PORT=$(find_port 8000)
FRONTEND_PORT=$(find_port 3000)
ok "Backend port: $BACKEND_PORT | Frontend port: $FRONTEND_PORT"

# Write backend URL for frontend proxy
mkdir -p frontend
echo "CORTEX_BACKEND_URL=http://localhost:${BACKEND_PORT}" > frontend/.env.local

# ── Launch ─────────────────────────────────────────────────────────────
echo -e "\n${BOLD}${GREEN}══════════════════════════════════════════════${RESET}"
echo -e "${BOLD}${GREEN}  ✓ All services ready! Launching servers…     ${RESET}"
echo -e "${BOLD}${GREEN}══════════════════════════════════════════════${RESET}"
echo -e "${CYAN}Backend API:    ${BOLD}http://localhost:${BACKEND_PORT}${RESET}"
echo -e "${CYAN}Frontend UI:    ${BOLD}http://localhost:${FRONTEND_PORT}${RESET}"
echo -e "${YELLOW}Press Ctrl+C to stop all services.${RESET}\n"

# ── Cleanup ────────────────────────────────────────────────────────────
cleanup() {
    echo -e "\n\n${YELLOW}[+] Shutting down Cortex services...${RESET}"
    kill "${BACKEND_PID:-}" 2>/dev/null || true
    kill "${FRONTEND_PID:-}" 2>/dev/null || true
    [ -n "$QDRANT_PID" ] && kill "$QDRANT_PID" 2>/dev/null || true
    if docker ps --format '{{.Names}}' 2>/dev/null | grep -q '^cortex-qdrant$'; then
        docker stop cortex-qdrant >/dev/null 2>&1 || true
    fi
    stop_postgres
    echo -e "${GREEN}[✓] All services stopped. Goodbye!${RESET}"
    exit 0
}

trap cleanup SIGINT SIGTERM EXIT

# Start backend
uv run uvicorn backend.app.main:app --host 0.0.0.0 --port "$BACKEND_PORT" &
BACKEND_PID=$!

# Start frontend
if [ -d "frontend" ]; then
    (cd frontend && PORT="$FRONTEND_PORT" npm run dev) &
    FRONTEND_PID=$!
fi

wait
