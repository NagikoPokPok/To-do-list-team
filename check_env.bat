@echo off
echo Checking virtual environment...
if exist "venv\Scripts\python.exe" (
    echo ✅ Virtual environment exists
    echo Running with venv Python...
    venv\Scripts\python.exe -c "import sys; print('Python path:', sys.executable)"
    venv\Scripts\python.exe -c "import fastapi; print('FastAPI version:', fastapi.__version__)"
    echo.
    echo Ready to run the app! Use:
    echo venv\Scripts\python.exe run_app.py --setup
    echo venv\Scripts\python.exe run_app.py --reload
) else (
    echo ❌ Virtual environment not found
    echo Please run: python -m venv venv
    echo Then run: venv\Scripts\pip.exe install -r requirements.txt
)
pause