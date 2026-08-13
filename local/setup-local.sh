#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
VENV_DIR="$BACKEND_DIR/.venv"

die() {
  printf 'error: %s\n' "$1" >&2
  exit 1
}

command -v python3 >/dev/null 2>&1 || die "Python 3 is required. Install Python 3.12 or newer."
command -v node >/dev/null 2>&1 || die "Node.js is required. Install Node.js 20 or newer."
command -v npm >/dev/null 2>&1 || die "npm is required. Install it with Node.js."

python_major="$(python3 -c 'import sys; print(sys.version_info.major)')"
python_minor="$(python3 -c 'import sys; print(sys.version_info.minor)')"
if [[ "$python_major" -lt 3 || ( "$python_major" -eq 3 && "$python_minor" -lt 12 ) ]]; then
  die "Python 3.12 or newer is required; found $(python3 --version)."
fi

node_major="$(node -p 'process.versions.node.split(".")[0]')"
if [[ "$node_major" -lt 20 ]]; then
  die "Node.js 20 or newer is required; found $(node --version)."
fi

printf '%s\n' "Creating backend virtual environment: $VENV_DIR"
python3 -m venv "$VENV_DIR"

printf '%s\n' 'Installing backend dependencies and test tools'
"$VENV_DIR/bin/python" -m pip install --upgrade pip
"$VENV_DIR/bin/pip" install -e "${BACKEND_DIR}[test]"

printf '%s\n' 'Installing frontend dependencies'
npm install --prefix "$FRONTEND_DIR"

printf '\n%s\n' 'Local dependencies are ready.'
printf '%s\n' "Activate Python: source $VENV_DIR/bin/activate"
printf '%s\n' "Run backend tests: cd $BACKEND_DIR && .venv/bin/pytest -q"
printf '%s\n' "Build frontend: cd $FRONTEND_DIR && npm run build"
printf '%s\n' 'Run the full stack: docker compose up -d --build'
