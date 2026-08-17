@echo off
echo Starting GrowZen Digital Plant Assistant...

if exist "plantai\Scripts\activate.bat" (
    call "plantai\Scripts\activate.bat"
)

cd digital-plant-assistant\backend
python app.py
pause
