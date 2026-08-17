@echo off
echo Starting GrowZen Digital Plant Assistant...

if exist "..\plantai\Scripts\activate.bat" (
    call "..\plantai\Scripts\activate.bat"
) else if exist "backend\venv\Scripts\activate.bat" (
    call "backend\venv\Scripts\activate.bat"
)

cd backend
python app.py
pause