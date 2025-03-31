@echo off
echo Starting Voice Agent with Ngrok

REM Start the Flask application in a new window
start cmd /k "python app.py"

REM Wait for Flask to start
echo Waiting for Flask to start (5 seconds)...
timeout /t 5 /nobreak > nul

REM Start Ngrok
echo Starting Ngrok tunnel to port 5000...
ngrok http 5000

echo Done! Close all windows when finished.