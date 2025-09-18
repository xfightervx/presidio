# Cross‑platform scripts to set up **uv**, sync the env, install deps, and run Uvicorn

Below are two scripts:

* `setup_uv.sh` for Linux/macOS (bash)
* `setup_uv.bat` for Windows (CMD)

Each script:

1. Checks if **uv** is installed (installs if missing).
2. Runs `uv sync` **only if needed** (i.e., if `.venv` doesn’t exist and `pyproject.toml` is present).
3. Skips `pip` and package installs when they’re already present.
4. Ensures `uvicorn` is available.
5. Starts `uvicorn core.backend:app --port 8000` **only if** port 8000 is free.

---

## `setup_uv.sh` (Linux/macOS)

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "[>>>] Checking for uv..."
UV_BIN=""
if command -v uv >/dev/null 2>&1; then
  UV_BIN="$(command -v uv)"
  echo "uv found at $UV_BIN"
else
  echo "uv not found; installing..."
  if command -v curl >/dev/null 2>&1; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
  elif command -v wget >/dev/null 2>&1; then
    wget -qO- https://astral.sh/uv/install.sh | sh
  else
    echo "Error: need curl or wget to install uv." >&2
    exit 1
  fi
fi

# Try to locate uv after install (covers shells where PATH wasn't refreshed)
if command -v uv >/dev/null 2>&1; then
  UV_BIN="$(command -v uv)"
elif [ -x "$HOME/.local/bin/uv" ]; then
  UV_BIN="$HOME/.local/bin/uv"; export PATH="$HOME/.local/bin:$PATH"
elif [ -x "$HOME/.cargo/bin/uv" ]; then
  UV_BIN="$HOME/.cargo/bin/uv"; export PATH="$HOME/.cargo/bin:$PATH"
fi

if [ -z "${UV_BIN}" ]; then
  echo "Error: uv installed but not found in PATH. Open a new shell or add it to PATH." >&2
  exit 1
fi

# Run uv sync only if a project is present and .venv is missing
if [ -f "pyproject.toml" ]; then
  if [ ! -d ".venv" ]; then
    echo "[>>>] Running 'uv sync'..."
    "$UV_BIN" sync
  else
    echo "[>>>] .venv already exists; skipping 'uv sync'."
  fi
else
  echo "[>>>] pyproject.toml not found; skipping 'uv sync'."
fi

# Ensure pip is importable inside the env (skip if already there)
echo "[>>>] Checking pip in the environment..."
if "$UV_BIN" run python -c "import pip" >/dev/null 2>&1; then
  echo "pip already available."
else
  echo "Installing pip..."
  "$UV_BIN" pip install pip
fi

# Ensure numpy, thinc, spacy (skip if already installed)
MISSING_PKGS=()
for pkg in numpy thinc spacy; do
  if "$UV_BIN" run python -c "import ${pkg}" >/dev/null 2>&1; then
    echo "${pkg} already installed; skipping."
  else
    MISSING_PKGS+=("${pkg}")
  fi
done

if [ ${#MISSING_PKGS[@]} -gt 0 ]; then
  echo "Installing missing packages: ${MISSING_PKGS[*]}"
  "$UV_BIN" pip install --upgrade --force-reinstall "${MISSING_PKGS[@]}"i

# Ensure uvicorn is present
if "$UV_BIN" run python -c "import uvicorn" >/dev/null 2>&1; then
  echo "uvicorn already installed."
else
  echo "Installing uvicorn..."
  "$UV_BIN" pip install uvicorn
fi

# Check whether port 8000 is already in use
echo "[>>>] Checking if port 8000 is free..."
PORT_BUSY=0
if command -v lsof >/dev/null 2>&1; then
  if lsof -iTCP:8000 -sTCP:LISTEN -t >/dev/null 2>&1; then PORT_BUSY=1; fi
elif command -v ss >/dev/null 2>&1; then
  if ss -ltn | grep -q ":8000"; then PORT_BUSY=1; fi
elif command -v netstat >/dev/null 2>&1; then
  if netstat -ltn 2>/dev/null | grep -q ":8000"; then PORT_BUSY=1; fi
fi

if [ "$PORT_BUSY" -eq 1 ]; then
  echo "Port 8000 appears to be in use; not starting uvicorn."
else
  echo "Starting uvicorn on port 8000..."
  exec "$UV_BIN" run uvicorn core.backend:app --port 8000
fi
```

**Usage**

```bash
chmod +x setup_uv.sh
./setup_uv.sh
```