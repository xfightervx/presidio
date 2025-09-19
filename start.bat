@echo off
setlocal

echo "[>>>] Checking for uv..."
where uv >NUL 2>&1
if not errorlevel 1 goto uv_found
echo "uv not found; installing..."
powershell -NoProfile -ExecutionPolicy Bypass -Command "iwr https://astral.sh/uv/install.ps1 -UseBasicParsing | iex"

rem Try to locate uv after installation
where uv >NUL 2>&1
if not errorlevel 1 goto uv_found

if exist "%USERPROFILE%\.local\bin\uv.exe" set "UV=%USERPROFILE%\.local\bin\uv.exe"
if not defined UV if exist "%USERPROFILE%\.cargo\bin\uv.exe" set "UV=%USERPROFILE%\.cargo\bin\uv.exe"
if not defined UV (
    echo "Error: uv installed but not found in PATH. Open a new terminal or add it to PATH."
    exit /b 1
)
goto uv_continue

:uv_found
for /f "delims=" %%i in ('where uv') do set "UV=%%i"
echo "uv found at %UV%"

:uv_continue
if not defined UV set "UV=uv"

rem Run uv sync only if project present and .venv missing
if not exist "pyproject.toml" goto no_pyproject
if not exist ".venv\Scripts\python.exe" goto run_uv_sync
goto venv_exists

:run_uv_sync
echo "[>>>] Running uv sync..."
call "%UV%" sync
goto :eof

:venv_exists
echo "[>>>] .venv already exists; skipping uv sync."
goto :pipfix

:no_pyproject
echo "[>>>] pyproject.toml not found; skipping uv sync."

:pipfix
.venv\Scripts\activate
uv pip install pip
uv pip install --upgrade --reinstall spacy thinc numpy