@echo off
REM Spark Core 4.1 - Stop Script (Windows)
REM Stop backend + frontend services

echo ================================================================
echo Spark Core 4.1 - Shutdown
echo ================================================================
echo.

echo Stopping services...

REM Kill processes on port 8001 (backend)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8001"') do taskkill /F /PID %%a >nul 2>nul
echo [OK] Backend stopped

REM Kill processes on port 3000 (frontend)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3000"') do taskkill /F /PID %%a >nul 2>nul
echo [OK] Frontend stopped

REM Kill any remaining Python/Node processes with "spark" or "uvicorn" in name
taskkill /F /FI "WINDOWTITLE eq Spark Backend*" >nul 2>nul
taskkill /F /FI "WINDOWTITLE eq Spark Frontend*" >nul 2>nul

echo.
echo ================================================================
echo Shutdown complete
echo ================================================================

pause
