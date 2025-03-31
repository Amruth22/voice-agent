#!/bin/bash

# Start the Twilio WebSocket server in the background
echo "Starting Twilio WebSocket server..."
python twilio_server.py &
SERVER_PID=$!

# Wait for the server to start
echo "Waiting for server to start (5 seconds)..."
sleep 5

# Start ngrok
echo "Starting ngrok tunnel to port 5000..."
ngrok http 5000

# When ngrok is closed, kill the server
echo "ngrok closed. Shutting down server..."
kill $SERVER_PID

echo "Done!"