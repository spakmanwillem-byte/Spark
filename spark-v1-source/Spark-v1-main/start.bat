@echo off
REM Spark Core 4.1 - Start Script (Windows)
REM One-click startup voor backend + frontend

echo ================================================================
echo Spark Core 4.1 - Startup
echo ================================================================
echo.

REM Get script directory
set "PROJECT_ROOT=%~dp0"
set "BACKEND_DIR=%PROJECT_ROOT%backend"
set "FRONTEND_DIR=%PROJECT_ROOT%frontend"

echo Project root: %PROJECT_ROOT%
echo.

REM Step 1: Check Dependencies
echo Step 1: Checking dependencies...
echo ---

REM Check Python
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python not found
    echo Install from: https://www.python.org/downloads/
    pause
    exit /b 1
)
python --version
echo [OK] Python found

REM Check Node
where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Node.js not found
    echo Install from: https://nodejs.org/
    pause
    exit /b 1
)
node --version
echo [OK] Node.js found

REM Check yarn
where yarn >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Yarn not found
    echo Install: npm install -g yarn
    pause
    exit /b 1
)
yarn --version
echo [OK] Yarn found

echo.

REM Step 2: Check ports
echo Step 2: Checking ports...
echo ---

REM Check if port 8001 is in use
netstat -ano | findstr ":8001" >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [WARNING] Port 8001 already in use
    echo Attempting to kill process...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8001"') do taskkill /F /PID %%a >nul 2>nul
    timeout /t 2 /nobreak >nul
)
echo [OK] Port 8001 available

REM Check if port 3000 is in use
netstat -ano | findstr ":3000" >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [WARNING] Port 3000 already in use
    echo Attempting to kill process...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3000"') do taskkill /F /PID %%a >nul 2>nul
    timeout /t 2 /nobreak >nul
)
echo [OK] Port 3000 available

echo.

REM Step 3: Install dependencies
echo Step 3: Installing dependencies (if needed)...
echo ---

REM Backend dependencies
cd /d "%BACKEND_DIR%"

if not exist "venv" (
    echo Creating Python virtual environment...
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

if not exist "venv\.dependencies_installed" (
    echo Installing Python dependencies...
    pip install -q -r requirements.txt
    echo. > venv\.dependencies_installed
    echo [OK] Backend dependencies installed
) else (
    echo [OK] Backend dependencies already installed
)

REM Frontend dependencies
cd /d "%FRONTEND_DIR%"

if not exist "node_modules" (
    echo Installing frontend dependencies...
    call yarn install
    echo [OK] Frontend dependencies installed
) else (
    echo [OK] Frontend dependencies already installed
)

echo.

REM Step 4: Start Backend
echo Step 4: Starting backend...
echo ---

cd /d "%BACKEND_DIR%"
call venv\Scripts\activate.bat

echo Starting backend with uvicorn...
start "Spark Backend" /B cmd /c "uvicorn server:app --host 0.0.0.0 --port 8001 --reload > backend.log 2>&1"

echo [OK] Backend started
echo     Log: %BACKEND_DIR%\backend.log

timeout /t 3 /nobreak >nul

echo.

REM Step 5: Start Frontend
echo Step 5: Starting frontend...
echo ---

cd /d "%FRONTEND_DIR%"

echo Starting frontend with yarn...
start "Spark Frontend" /B cmd /c "yarn start > frontend.log 2>&1"

echo [OK] Frontend started
echo     Log: %FRONTEND_DIR%\frontend.log

echo.
echo ================================================================
echo Spark Core 4.1 - Startup Complete!
echo ================================================================
echo.
echo Backend:  http://localhost:8001
echo Frontend: http://localhost:3000
echo.
echo Status check:
echo   Backend:  type %BACKEND_DIR%\backend.log
echo   Frontend: type %FRONTEND_DIR%\frontend.log
echo.
echo To stop: stop.bat
echo.
echo ================================================================

pause
