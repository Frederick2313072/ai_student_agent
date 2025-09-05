@echo off
title AI Student Agent - Service Launcher

echo ===================================================
echo  Starting AI Student Agent Services...
echo ===================================================
echo.

REM 检查虚拟环境是否存在
IF NOT EXIST .venv\Scripts\activate (
    echo Error: Virtual environment not found at .venv\Scripts\activate
    echo Please run 'python -m venv .venv' to create it first.
    pause
    exit /b
)

echo Activating virtual environment...
call .venv\Scripts\activate

echo.
echo Starting FastAPI Backend API on port 8000...
start "Backend API" cmd /k "uvicorn main:app --reload --port 8000"

echo.


echo.
echo Starting Streamlit Frontend on port 8501...
start "Frontend UI" cmd /k "streamlit run ui.py --server.port 8501 --server.headless true"

echo.
echo =================================================================
echo  All services are launching in separate windows.
echo  You can monitor the logs in each respective window.
echo.
echo  This launcher window will close in 5 seconds.
echo =================================================================

timeout /t 5
