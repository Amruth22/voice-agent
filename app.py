from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO
import os
import json
import logging
from datetime import datetime, timedelta, timezone
import base64
import secrets
from dotenv import load_dotenv
import sys

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Flask app setup
app = Flask(__name__, static_folder="./static", static_url_path="/")
app.secret_key = secrets.token_hex(16)
socketio = SocketIO(app, cors_allowed_origins="*")

# Mock data for Vercel deployment
MOCK_AVAILABLE_SLOTS = [
    (datetime.now() + timedelta(days=1, hours=10)).isoformat(),
    (datetime.now() + timedelta(days=1, hours=14)).isoformat(),
    (datetime.now() + timedelta(days=2, hours=11)).isoformat(),
    (datetime.now() + timedelta(days=2, hours=15)).isoformat(),
    (datetime.now() + timedelta(days=3, hours=9)).isoformat(),
    (datetime.now() + timedelta(days=3, hours=13)).isoformat(),
]

MOCK_CUSTOMER_DATA = {
    "name": "John Doe",
    "email": "john.doe@example.com",
    "phone": "555-123-4567",
    "appointment_type": "Consultation",
    "appointment_time": (datetime.now() + timedelta(days=1, hours=10)).isoformat()
}

# Flask routes
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/devices", methods=["GET"])
def get_audio_devices():
    # Mock audio devices for Vercel deployment
    return jsonify({
        "input": [
            {"index": 0, "name": "Default Microphone", "deviceId": 0},
            {"index": 1, "name": "Built-in Microphone", "deviceId": 1}
        ],
        "output": [
            {"index": 0, "name": "Default Speaker", "deviceId": 0},
            {"index": 1, "name": "Built-in Speaker", "deviceId": 1}
        ]
    })

@app.route("/api/status", methods=["GET"])
def get_status():
    return jsonify({
        "status": "online",
        "version": "1.0.0",
        "environment": "vercel",
        "timestamp": datetime.now().isoformat()
    })

@socketio.on("start_voice_agent")
def handle_start_voice_agent(data=None):
    # Emit a welcome message
    socketio.emit("conversation_update", {
        "role": "assistant",
        "content": "Hello! I'm your appointment scheduling assistant. How can I help you today? (Note: This is a demo version running on Vercel with limited functionality.)"
    })

@socketio.on("stop_voice_agent")
def handle_stop_voice_agent():
    # Emit a goodbye message
    socketio.emit("conversation_update", {
        "role": "assistant",
        "content": "Thank you for using our service. Goodbye!"
    })

@socketio.on("send_text")
def handle_send_text(data):
    """Handle text input from the user"""
    text = data.get("text", "")
    if text:
        # Echo the user's message
        socketio.emit("conversation_update", {
            "role": "user",
            "content": text
        })
        
        # Process the message and respond
        process_user_message(text)

def process_user_message(text):
    """Process user message and generate a response"""
    text_lower = text.lower()
    
    # Show typing indicator
    socketio.emit("typing_indicator", {"typing": True})
    
    # Simulate processing delay
    import time
    time.sleep(1.5)
    
    # Check for appointment-related keywords
    if "schedule" in text_lower or "appointment" in text_lower or "book" in text_lower:
        # Respond with available slots
        response = "I'd be happy to help you schedule an appointment. Here are some available times:\n\n"
        for i, slot in enumerate(MOCK_AVAILABLE_SLOTS[:3], 1):
            slot_dt = datetime.fromisoformat(slot)
            response += f"{i}. {slot_dt.strftime('%A, %B %d at %I:%M %p')}\n"
        response += "\nWhich time works best for you?"
        
    elif "slot" in text_lower or "time" in text_lower or "1" in text_lower or "first" in text_lower:
        # Confirm appointment
        slot_dt = datetime.fromisoformat(MOCK_AVAILABLE_SLOTS[0])
        formatted_time = slot_dt.strftime('%A, %B %d at %I:%M %p')
        response = f"Great! I've scheduled your appointment for {formatted_time}. Can I get your name and email address?"
        
    elif "name" in text_lower or "email" in text_lower or "contact" in text_lower or "@" in text_lower:
        # Confirm customer information
        response = "Thank you for providing your information. Your appointment has been confirmed!"
        
        # Emit appointment scheduled event
        socketio.emit("appointment_scheduled", {
            "customer": MOCK_CUSTOMER_DATA,
            "appointment": {
                "status": "success",
                "event_id": "mock-123",
                "event_link": "https://calendar.google.com",
                "appointment_time": MOCK_CUSTOMER_DATA["appointment_time"]
            }
        })
        
    elif "help" in text_lower or "can you" in text_lower or "what" in text_lower:
        # Provide help information
        response = "I can help you schedule appointments. You can ask me to:\n\n" + \
                  "1. Schedule an appointment\n" + \
                  "2. Check available time slots\n" + \
                  "3. Confirm your booking\n\n" + \
                  "This is a demo version running on Vercel with limited functionality."
        
    else:
        # Default response
        response = "I'm here to help you schedule appointments. Would you like to book a time to view our properties?"
    
    # Send the response
    socketio.emit("conversation_update", {
        "role": "assistant",
        "content": response
    })
    
    # Turn off typing indicator
    socketio.emit("typing_indicator", {"typing": False})

# Vercel serverless function handler
@app.route("/api/serverless-function", methods=["POST"])
def serverless_function():
    data = request.json
    return jsonify({
        "received": data,
        "message": "This is a serverless function response",
        "timestamp": datetime.now().isoformat()
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port)