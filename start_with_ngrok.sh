#!/bin/bash

# Start the Flask application in the background
echo "Starting Flask application..."
python app.py &
FLASK_PID=$!

# Wait for Flask to start
echo "Waiting for Flask to start (5 seconds)..."
sleep 5

# Start Ngrok
echo "Starting Ngrok tunnel to port 5000..."
ngrok http 5000

# When Ngrok is closed, kill the Flask application
echo "Ngrok closed. Shutting down Flask application..."
kill $FLASK_PID

echo "Done!"