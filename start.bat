@echo off
setlocal enabledelayedexpansion


echo [>>>] Checking for uv...
where uv >NUL 2>&1
if %ERRORLEVEL% EQU 0 (
for /f "delims=" %%i in ('where uv') do set "UV=%%i"
echo uv found at "%UV%"
) else (
echo uv not found; installing...
powershell -NoProfile -ExecutionPolicy Bypass -Command "iwr https://astral.sh/uv/install.ps1 -UseBasicParsing ^| iex"
rem Try to locate uv after installation
where uv >NUL 2>&1
if %ERRORLEVEL% EQU 0 (
for /f "delims=" %%i in ('where uv') do set "UV=%%i"
) else (
if exist "%USERPROFILE%\.local\bin\uv.exe" set "UV=%USERPROFILE%\.local\bin\uv.exe"
if not defined UV if exist "%USERPROFILE%\.cargo\bin\uv.exe" set "UV=%USERPROFILE%\.cargo\bin\uv.exe"
)
if not defined UV (
echo Error: uv installed but not found in PATH. Open a new terminal or add it to PATH.
exit /b 1
)
)
if not defined UV set "UV=uv"


rem Run uv sync only if project present and .venv missing
if exist "pyproject.toml" (
if not exist ".venv\Scripts\python.exe" (
echo [>>>] Running "uv sync"...
"%UV%" sync
) else (
echo [>>>] .venv already exists; skipping "uv sync".
)
) else (
echo [>>>] pyproject.toml not found; skipping "uv sync".
)