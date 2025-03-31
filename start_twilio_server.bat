@echo off
echo Starting Twilio WebSocket Server with ngrok

REM Start the Twilio WebSocket server in a new window
start cmd /k "python twilio_server.py"

REM Wait for the server to start
echo Waiting for server to start (5 seconds)...
timeout /t 5 /nobreak > nul

REM Start ngrok
echo Starting ngrok tunnel to port 5000...
ngrok http 5000

echo Done! Close all windows when finished.