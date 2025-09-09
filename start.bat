
@echo off
echo Link Start...
echo.
echo Checking Requirements...
python -c "import flask, manim, numpy" 2>nul
if %errorlevel% neq 0 (
    echo Error: Requirements Not Found
    echo Run: pip install -r requirements.txt
    pause
    exit /b 1
)

echo Over!
echo.
echo Web Server Start...
echo please click: http://localhost:5000
echo.
echo Press Ctrl+C to stop
echo.

python app.py

pause
