@echo off
chcp 65001 >nul 2>&1

echo ============================================
echo  LifeSync AI - Starting Backend + Frontend
echo ============================================
echo.

start "Backend" cmd /k "cd /d C:\yssong\KDT-FT-team3-Chainers\MOMA\lifesync-ai && .venv\Scripts\activate && uvicorn backend.app.main:app --reload --port 8000"

timeout /t 3 /nobreak >nul

start "Frontend" cmd /k "cd /d C:\yssong\KDT-FT-team3-Chainers\MOMA\lifesync-ai\frontend && npm run dev"

echo.
echo  Backend:  http://localhost:8000
echo  Frontend: http://localhost:5173
echo.
echo  Press Ctrl+C in each window to stop.
