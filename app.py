from flask import Flask, render_template, request, jsonify, session, copy_current_request_context
from flask_socketio import SocketIO
import os
import asyncio
import json
import logging
import threading
import queue
import time
from datetime import datetime, timedelta, timezone
import base64
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle
import secrets
from functools import wraps
from dotenv import load_dotenv
import sys
import websockets
import traceback
import eventlet

# Patch for eventlet with asyncio
eventlet.monkey_patch()

# Try to import PyAudio, but provide a fallback if it's not available
try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
    logger.info("PyAudio is available")
except ImportError:
    PYAUDIO_AVAILABLE = False
    logger.warning("PyAudio is not available. Audio functionality will be limited.")
    # Create a mock PyAudio class for compatibility
    class MockPyAudio:
        def __init__(self):
            pass
        
        def open(self, *args, **kwargs):
            class MockStream:
                def start_stream(self):
                    pass
                def stop_stream(self):
                    pass
                def close(self):
                    pass
            return MockStream()
        
        def get_host_api_info_by_index(self, *args, **kwargs):
            return {"deviceCount": 0}
        
        def get_device_info_by_host_api_device_index(self, *args, **kwargs):
            return {"maxInputChannels": 0, "name": "Mock Device"}
        
        def get_device_count(self):
            return 0
        
        def terminate(self):
            pass
    
    # Replace pyaudio with our mock if it's not available
    pyaudio = MockPyAudio()

try:
    import janus
except ImportError:
    # Create a mock Janus Queue for compatibility
    class MockJanus:
        class Queue:
            def __init__(self):
                self.async_q = asyncio.Queue()
                self.sync_q = queue.Queue()
        
        @staticmethod
        def Queue():
            return MockJanus.Queue()
    
    janus = MockJanus

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
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(16))
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Google Calendar API scopes
SCOPES = ['https://www.googleapis.com/auth/calendar']

# Deepgram Voice Agent URL
VOICE_AGENT_URL = "wss://agent.deepgram.com/agent"

# Audio settings
USER_AUDIO_SAMPLE_RATE = 48000
USER_AUDIO_SECS_PER_CHUNK = 0.05
USER_AUDIO_SAMPLES_PER_CHUNK = round(USER_AUDIO_SAMPLE_RATE * USER_AUDIO_SECS_PER_CHUNK)

AGENT_AUDIO_SAMPLE_RATE = 16000
AGENT_AUDIO_BYTES_PER_SEC = 2 * AGENT_AUDIO_SAMPLE_RATE
name = os.environ.get("CUSTOMER_NAME", "Aamruth")
email = os.environ.get("CUSTOMER_EMAIL", 'chatgptplus1999@gmail.com')

# Template for the prompt that will be formatted with current date
PROMPT_TEMPLATE = """You are a friendly and professional real estate appointment scheduler for Premium Properties. Your role is to assist potential buyers in scheduling property viewings in Google Calendar.

CURRENT DATE AND TIME CONTEXT:
Today is {current_date}. Use this as context when discussing appointments. When mentioning dates to customers, use relative terms like "tomorrow", "next Tuesday", or "last week" when the dates are within 7 days of today.

CUSTOMER INFORMATION:
The customer you're speaking with is {name}, and their email is {email}. Make sure to acknowledge this information and confirm it early in the conversation.

PERSONALITY & TONE:
- Be warm, professional, and conversational
- Use natural, flowing speech (avoid bullet points or listing)
- Show empathy and patience
- Sound enthusiastic about the property
- Ask whether they're interested in purchasing the property before scheduling

CONVERSATION FLOW:
1. Greet the customer by name and introduce yourself as a real estate scheduling assistant
2. Ask about which property they're interested in viewing (suggest a luxury property if they don't specify)
3. Ask if they're interested in purchasing the property
4. Only if they express interest in buying, proceed to scheduling
5. Check availability and offer time slots
6. Confirm the appointment details

INFORMATION TO COLLECT:
- Property of interest (if not specified, suggest "our luxury beachfront villa in Malibu")
- Confirmation of purchase interest
- Preferred date and time for the viewing

FUNCTION RESPONSES:
When receiving function results, format responses naturally:

1. For available slots:
   - "I have a few openings next week to view the property. Would you prefer Tuesday at 2 PM or Wednesday at 3 PM?"

2. For appointment confirmation:
   - "Great! I've scheduled your property viewing for [date] at [time]. You'll receive an email confirmation shortly."

3. For errors:
   - Never expose technical details
   - Say something like "I'm having trouble accessing the calendar right now" or "Could you please try again?"

EXAMPLES OF GOOD RESPONSES:
✓ "Hello {name}! I understand you're interested in our beachfront property. Are you considering purchasing it?"
✓ "Before we schedule a viewing, may I ask if you're looking to buy this property or just exploring options?"
✓ "Since you're interested in purchasing, let me check what viewing times are available next week."
✓ "I've found a few available slots to view the property. Would Tuesday at 2 PM work for you?"

FILLER PHRASES:
When you need to indicate you're looking something up, use phrases like:
- "Let me check the viewing calendar for available slots..."
- "One moment while I schedule that property viewing..."
- "I'm checking availability for that date..."
"""
# Voice agent settings
VOICE = "aura-asteria-en"

# Function definitions for the voice agent
FUNCTION_DEFINITIONS = [
    {
        "name": "get_customer_info",
        "description": "Get information about the customer for scheduling an appointment",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Customer's full name"
                },
                "email": {
                    "type": "string",
                    "description": "Customer's email address for calendar invitation"
                },
                "phone": {
                    "type": "string",
                    "description": "Customer's phone number (optional)"
                }
            },
            "required": ["name", "email"]
        }
    },
    {
        "name": "check_availability",
        "description": "Check available appointment slots within a date range",
        "parameters": {
            "type": "object",
            "properties": {
                "start_date": {
                    "type": "string",
                    "description": "Start date in ISO format (YYYY-MM-DDTHH:MM:SS). Usually today's date for immediate availability checks."
                },
                "end_date": {
                    "type": "string",
                    "description": "End date in ISO format. Optional - defaults to 7 days after start_date."
                }
            },
            "required": ["start_date"]
        }
    },
    {
        "name": "schedule_appointment",
        "description": "Schedule a new appointment in Google Calendar",
        "parameters": {
            "type": "object",
            "properties": {
                "appointment_type": {
                    "type": "string",
                    "description": "Type of appointment",
                    "enum": ["Consultation", "Follow-up", "Review", "Planning"]
                },
                "appointment_time": {
                    "type": "string",
                    "description": "Appointment date and time in ISO format (YYYY-MM-DDTHH:MM:SS)"
                }
            },
            "required": ["appointment_type", "appointment_time"]
        }
    },
    {
        "name": "end_conversation",
        "description": "End the conversation after scheduling is complete",
        "parameters": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Farewell message to display to the user"
                }
            },
            "required": ["message"]
        }
    }
]

# Customer data class
class CustomerData:
    """Class to store and validate customer data"""
    
    def __init__(self):
        self.name = None
        self.email = None
        self.phone = None
        self.customer_id = None
        self.appointment_type = None
        self.appointment_time = None
    
    def is_valid_for_appointment(self):
        """Check if we have enough data to schedule an appointment"""
        return all([
            self.name,
            self.email,
            self.appointment_type,
            self.appointment_time
        ])
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "customer_id": self.customer_id,
            "appointment_type": self.appointment_type,
            "appointment_time": self.appointment_time
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create from dictionary"""
        customer = cls()
        customer.name = data.get("name")
        customer.email = data.get("email")
        customer.phone = data.get("phone")
        customer.customer_id = data.get("customer_id")
        customer.appointment_type = data.get("appointment_type")
        customer.appointment_time = data.get("appointment_time")
        return customer


# Helper function to ensure RFC3339 format for dates
def ensure_rfc3339_format(date_string):
    """Ensure the date string is in RFC3339 format with timezone"""
    # Make sure it has time component
    if 'T' not in date_string:
        date_string = f"{date_string}T00:00:00"

    # If already has timezone info (Z or +/-), return as is
    if date_string.endswith('Z') or '+' in date_string[10:] or '-' in date_string[10:]:
        return date_string

    # Otherwise, add 'Z' for UTC
    return date_string + 'Z'


# Google Calendar Scheduler
class GoogleCalendarScheduler:
    """Class to handle Google Calendar operations"""
    
    def __init__(self, credentials_file='credentials.json', token_file='token.pickle'):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        
        # For Heroku, try to use environment variables for credentials
        self.use_env_credentials = os.environ.get("USE_ENV_CREDENTIALS", "false").lower() == "true"
    
    def authenticate(self):
        """Authenticate with Google Calendar API"""
        try:
            logger.info(f"Authenticating with Google Calendar API")
            
            creds = None
            
            # Try to use environment variables for credentials if configured
            if self.use_env_credentials:
                logger.info("Using environment variables for credentials")
                creds_info = os.environ.get("GOOGLE_CREDENTIALS")
                if creds_info:
                    import json
                    creds_dict = json.loads(creds_info)
                    creds = Credentials.from_authorized_user_info(creds_dict, SCOPES)
                    logger.info(f"Credentials loaded from environment, expired: {creds.expired if creds else 'N/A'}")
            else:
                # Load existing token if available
                if os.path.exists(self.token_file):
                    logger.info("Loading existing token")
                    with open(self.token_file, 'rb') as token:
                        creds = pickle.load(token)
                    logger.info(f"Token loaded, expired: {creds.expired if creds else 'N/A'}")
            
            # Refresh token if expired
            if creds and creds.expired and creds.refresh_token:
                logger.info("Refreshing expired token")
                creds.refresh(Request())
                logger.info("Token refreshed")
                
                # Save refreshed token if not using environment variables
                if not self.use_env_credentials:
                    with open(self.token_file, 'wb') as token:
                        pickle.dump(creds, token)
                    logger.info("Refreshed token saved")
            # Otherwise, get new credentials
            elif not creds:
                logger.info("No token found, getting new credentials")
                
                if self.use_env_credentials:
                    logger.error("No credentials in environment variables")
                    return False
                
                if not os.path.exists(self.credentials_file):
                    logger.error(f"Credentials file not found: {self.credentials_file}")
                    return False
                
                # Set this to allow insecure local redirect
                os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
                
                # For personal use, we can use a more permissive client
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, 
                    SCOPES,
                    redirect_uri='http://localhost:8080/'
                )
                
                # Run the local server with a specific port
                creds = flow.run_local_server(port=8080)
                logger.info("New credentials obtained")
                
                # Save credentials for future use
                with open(self.token_file, 'wb') as token:
                    pickle.dump(creds, token)
                logger.info("New token saved")
            
            # Build the service
            self.service = build('calendar', 'v3', credentials=creds)
            logger.info("Google Calendar service built successfully")
            return True
        except Exception as e:
            logger.error(f"Error authenticating with Google Calendar: {e}")
            logger.error(traceback.format_exc())
            return False
    
    async def get_available_slots(self, start_date, end_date=None, calendar_id='primary'):
        """Get available appointment slots"""
        logger.info(f"Getting available slots from {start_date} to {end_date or 'week later'}")

        if not self.service:
            logger.info("No service, authenticating")
            if not self.authenticate():
                logger.error("Failed to authenticate with Google Calendar")
                return {"error": "Failed to authenticate with Google Calendar"}

        if not end_date:
            # Make sure to create a datetime with time component
            end_date = (datetime.fromisoformat(start_date.replace('Z', '+00:00') if start_date.endswith('Z') else start_date) + timedelta(days=7)).isoformat()
            logger.info(f"End date not provided, using {end_date}")

        # Ensure dates are in RFC3339 format with timezone
        start_date_rfc = ensure_rfc3339_format(start_date)
        end_date_rfc = ensure_rfc3339_format(end_date)

        logger.info(f"Using RFC3339 dates: {start_date_rfc} to {end_date_rfc}")

        # Get busy times from calendar
        body = {
            "timeMin": start_date_rfc,
            "timeMax": end_date_rfc,
            "items": [{"id": calendar_id}]
        }

        try:
            logger.info(f"Querying freebusy with body: {body}")
            events_result = self.service.freebusy().query(body=body).execute()
            busy_times = events_result['calendars'][calendar_id]['busy']
            logger.info(f"Found {len(busy_times)} busy times")

            # Generate all possible slots (9 AM to 5 PM, 1-hour slots)
            all_slots = []
            current = datetime.fromisoformat(start_date.replace('Z', '+00:00') if start_date.endswith('Z') else start_date)
            end = datetime.fromisoformat(end_date.replace('Z', '+00:00') if end_date.endswith('Z') else end_date)

            while current <= end:
                if current.hour >= 9 and current.hour < 17:
                    # Skip weekends
                    if current.weekday() < 5:  # 0-4 are Monday to Friday
                        slot_time = current.isoformat()
                        all_slots.append(slot_time)
                current += timedelta(hours=1)

            logger.info(f"Generated {len(all_slots)} possible slots")

            # Filter out busy slots
            available_slots = []
            for slot in all_slots:
                slot_dt = datetime.fromisoformat(slot)
                slot_end = (slot_dt + timedelta(hours=1)).isoformat()

                # Convert to UTC if needed (make sure both are aware datetimes)
                if not slot.endswith('Z') and not '+' in slot:
                    # Make slot_dt timezone-aware (assuming UTC)
                    slot_dt = slot_dt.replace(tzinfo=timezone.utc)

                is_available = True
                for busy in busy_times:
                    busy_start = datetime.fromisoformat(busy['start'].replace('Z', '+00:00'))
                    busy_end = datetime.fromisoformat(busy['end'].replace('Z', '+00:00'))

                    # Now both are timezone-aware, comparison will work
                    if (slot_dt >= busy_start and slot_dt < busy_end) or \
                    (slot_dt < busy_start and datetime.fromisoformat(slot_end).replace(tzinfo=timezone.utc) > busy_start):
                        is_available = False
                        break

                if is_available:
                    available_slots.append(slot)

            logger.info(f"Found {len(available_slots)} available slots")
            return {"available_slots": available_slots}

        except Exception as e:
            logger.error(f"Error getting available slots: {e}")
            logger.error(traceback.format_exc())
            return {"error": f"Failed to get available slots: {str(e)}"}
    
    async def schedule_appointment(self, customer_data, calendar_id='primary'):
        """Schedule an appointment in Google Calendar"""
        logger.info(f"Scheduling appointment for {customer_data.name}")
        
        if not self.service:
            logger.info("No service, authenticating")
            if not self.authenticate():
                logger.error("Failed to authenticate with Google Calendar")
                return {"error": "Failed to authenticate with Google Calendar"}
        
        if not customer_data.is_valid_for_appointment():
            logger.error("Incomplete customer data for appointment")
            return {"error": "Incomplete customer data for appointment"}
        
        # Ensure appointment time is in RFC3339 format
        appointment_time_rfc = ensure_rfc3339_format(customer_data.appointment_time)
        appointment_end_time_rfc = ensure_rfc3339_format(
            (datetime.fromisoformat(customer_data.appointment_time.replace('Z', '+00:00') 
                                   if customer_data.appointment_time.endswith('Z') 
                                   else customer_data.appointment_time) 
             + timedelta(hours=1)).isoformat()
        )
        
        # Create event
        event = {
            'summary': f"{customer_data.appointment_type} with {customer_data.name}",
            'description': f"Phone: {customer_data.phone or 'N/A'}",
            'start': {
                'dateTime': appointment_time_rfc,
                'timeZone': 'America/New_York',  # Adjust timezone as needed
            },
            'end': {
                'dateTime': appointment_end_time_rfc,
                'timeZone': 'America/New_York',  # Adjust timezone as needed
            },
            'attendees': [
                {'email': customer_data.email},
            ],
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},
                    {'method': 'popup', 'minutes': 30},
                ],
            },
        }
        
        try:
            logger.info(f"Creating event: {event}")
            event = self.service.events().insert(calendarId=calendar_id, body=event, sendUpdates='all').execute()
            logger.info(f"Event created: {event.get('htmlLink')}")
            
            return {
                "status": "success",
                "event_id": event.get('id'),
                "event_link": event.get('htmlLink'),
                "appointment_time": customer_data.appointment_time
            }
            
        except Exception as e:
            logger.error(f"Error scheduling appointment: {e}")
            logger.error(traceback.format_exc())
            return {"error": f"Failed to schedule appointment: {str(e)}"}


# Mock Calendar Scheduler for testing without Google Calendar
class MockCalendarScheduler:
    """Mock implementation of calendar operations for testing"""
    
    def __init__(self):
        self.appointments = []
    
    async def get_available_slots(self, start_date, end_date=None, calendar_id='primary'):
        """Get mock available appointment slots"""
        logger.info(f"Getting mock available slots from {start_date} to {end_date or 'week later'}")
        
        if not end_date:
            end_date = (datetime.fromisoformat(start_date) + timedelta(days=7)).isoformat()
        
        # Generate available slots (9 AM to 5 PM, 1-hour slots)
        available_slots = []
        current = datetime.fromisoformat(start_date.replace('Z', '+00:00') if start_date.endswith('Z') else start_date)
        end = datetime.fromisoformat(end_date.replace('Z', '+00:00') if end_date.endswith('Z') else end_date)
        
        while current <= end:
            if current.hour >= 9 and current.hour < 17:
                # Skip weekends
                if current.weekday() < 5:  # 0-4 are Monday to Friday
                    slot_time = current.isoformat()
                    available_slots.append(slot_time)
            current += timedelta(hours=1)
        
        logger.info(f"Generated {len(available_slots)} mock available slots")
        return {"available_slots": available_slots}
    
    async def schedule_appointment(self, customer_data, calendar_id='primary'):
        """Schedule a mock appointment"""
        logger.info(f"Scheduling mock appointment for {customer_data.name}")
        
        if not customer_data.is_valid_for_appointment():
            logger.error("Incomplete customer data for appointment")
            return {"error": "Incomplete customer data for appointment"}
        
        # Create a mock appointment
        appointment = {
            'id': f"mock-{len(self.appointments) + 1}",
            'summary': f"{customer_data.appointment_type} with {customer_data.name}",
            'start': customer_data.appointment_time,
            'end': (datetime.fromisoformat(customer_data.appointment_time.replace('Z', '+00:00') 
                                         if customer_data.appointment_time.endswith('Z') 
                                         else customer_data.appointment_time) 
                   + timedelta(hours=1)).isoformat(),
            'attendees': [customer_data.email],
            'link': f"https://example.com/calendar/event/{len(self.appointments) + 1}"
        }
        
        self.appointments.append(appointment)
        logger.info(f"Mock appointment created: {appointment}")
        
        return {
            "status": "success",
            "event_id": appointment['id'],
            "event_link": appointment['link'],
            "appointment_time": customer_data.appointment_time
        }


# Global storage for customer data
customer_data_store = {}

# Voice Agent class
class VoiceAgent:
    def __init__(self):
    # Try to get the current event loop or create a new one
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        self.mic_audio_queue = asyncio.Queue()
        self.speaker = None
        self.ws = None
        self.is_running = False
        self.loop = loop  # Store the loop
        self.audio = None
        self.stream = None
        self.input_device_id = None
        self.output_device_id = None
        self.customer_data = CustomerData()
        self.session_id = secrets.token_hex(8)  # Generate a unique session ID
        
        # Use mock scheduler if USE_MOCK_CALENDAR is set to True
        if os.environ.get("USE_MOCK_CALENDAR", "false").lower() == "true":
            logger.info("Using mock calendar scheduler")
            self.calendar_scheduler = MockCalendarScheduler()
        else:
            logger.info("Using Google Calendar scheduler")
            self.calendar_scheduler = GoogleCalendarScheduler()
        
    def set_loop(self, loop):
        self.loop = loop

    async def setup(self):
        dg_api_key = os.environ.get("DEEPGRAM_API_KEY")
        if dg_api_key is None:
            logger.error("DEEPGRAM_API_KEY env var not present")
            return False

        try:
            # Format the prompt with the current date
            current_date = datetime.now().strftime("%A, %B %d, %Y")
            formatted_prompt = PROMPT_TEMPLATE.format(
            current_date=current_date,
            name=name,  # Using the global name variable
            email=email  # Using the global email variable
        )
            # Create settings dictionary
            settings = {
                "type": "SettingsConfiguration",
                "audio": {
                    "input": {
                        "encoding": "linear16",
                        "sample_rate": USER_AUDIO_SAMPLE_RATE,
                    },
                    "output": {
                        "encoding": "linear16",
                        "sample_rate": AGENT_AUDIO_SAMPLE_RATE,
                        "container": "none",
                    },
                },
                "agent": {
                    "listen": {"model": "nova-2"},
                    "think": {
                        "provider": {"type": "open_ai"},
                        "model": "gpt-4o-mini",
                        "instructions": formatted_prompt,
                        "functions": FUNCTION_DEFINITIONS,
                    },
                    "speak": {"model": VOICE},
                },
                "context": {
                    "messages": [
                        {
                            "role": "assistant",
                            "content": f"Hello {name}! I'm your appointment scheduling assistant. How can I help you today?",
                        }
                    ],
                    "replay": True,
                },
            }
            
            # Connect to Deepgram using websockets directly
            logger.info("Connecting to Deepgram Voice Agent API...")
            headers = {"Authorization": f"Token {dg_api_key}"}
            self.ws = await websockets.connect(VOICE_AGENT_URL, extra_headers=headers)
            
            # Send settings
            await self.ws.send(json.dumps(settings))
            
            # Wait for settings applied confirmation
            response = await self.ws.recv()
            response_json = json.loads(response)
            if response_json.get("type") == "SettingsApplied":
                logger.info("Settings applied successfully")
            else:
                logger.info(f"Received response: {response_json}")
                
            logger.info("Deepgram connection established successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Deepgram: {e}")
            logger.error(traceback.format_exc())
            return False

    def audio_callback(self, input_data, frame_count, time_info, status_flag):
        if self.is_running and self.loop and not self.loop.is_closed():
            try:
                future = asyncio.run_coroutine_threadsafe(
                    self.mic_audio_queue.put(input_data), self.loop
                )
                future.result(timeout=1)  # Add timeout to prevent blocking
            except Exception as e:
                logger.error(f"Error in audio callback: {e}")
        return (input_data, pyaudio.paContinue)

    async def start_microphone(self):
        if not PYAUDIO_AVAILABLE:
            logger.warning("PyAudio is not available. Using mock microphone.")
            return None, None
            
        try:
            self.audio = pyaudio.PyAudio()

            # List available input devices
            info = self.audio.get_host_api_info_by_index(0)
            numdevices = info.get("deviceCount")
            input_device_index = None

            for i in range(0, numdevices):
                device_info = self.audio.get_device_info_by_host_api_device_index(0, i)
                if device_info.get("maxInputChannels") > 0:
                    logger.info(f"Input Device {i}: {device_info.get('name')}")
                    # Use selected device if available
                    if (
                        self.input_device_id
                        and str(device_info.get("deviceId")) == self.input_device_id
                    ):
                        input_device_index = i
                        break
                    # Otherwise use first available device
                    elif input_device_index is None:
                        input_device_index = i

            if input_device_index is None:
                logger.warning("No input device found. Using mock microphone.")
                return None, None

            self.stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=USER_AUDIO_SAMPLE_RATE,
                input=True,
                input_device_index=input_device_index,
                frames_per_buffer=USER_AUDIO_SAMPLES_PER_CHUNK,
                stream_callback=self.audio_callback,
            )
            self.stream.start_stream()
            logger.info("Microphone started successfully")
            return self.stream, self.audio
        except Exception as e:
            logger.error(f"Error starting microphone: {e}")
            if self.audio:
                self.audio.terminate()
            return None, None

    def cleanup(self):
        """Clean up audio resources"""
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except Exception as e:
                logger.error(f"Error closing audio stream: {e}")

        if self.audio:
            try:
                self.audio.terminate()
            except Exception as e:
                logger.error(f"Error terminating audio: {e}")
                
        if self.ws:
            try:
                asyncio.run_coroutine_threadsafe(self.ws.close(), self.loop)
            except Exception as e:
                logger.error(f"Error closing Deepgram connection: {e}")

    async def sender(self):
        try:
            while self.is_running:
                data = await self.mic_audio_queue.get()
                if self.ws and data:
                    await self.ws.send(data)
        except Exception as e:
            logger.error(f"Error in sender: {e}")

    async def handle_function_call(self, function_name, function_call_id, parameters):
        """Handle function calls from the voice agent"""
        logger.info(f"Function call received: {function_name}")
        logger.info(f"Parameters: {parameters}")
        
        result = {}
        
        try:
            if function_name == "get_customer_info":
                # Store customer info
                self.customer_data.name = parameters.get("name")
                self.customer_data.email = parameters.get("email")
                self.customer_data.phone = parameters.get("phone")
                
                # Store in global dictionary instead of session
                customer_data_store[self.session_id] = self.customer_data.to_dict()
                
                result = {
                    "status": "success",
                    "message": f"Customer information stored for {self.customer_data.name}"
                }
                
            elif function_name == "check_availability":
                # Check available slots
                start_date = parameters.get("start_date")
                end_date = parameters.get("end_date")
                
                # Parse the date if it's not in ISO format
                try:
                    # Try to parse as ISO format
                    datetime.fromisoformat(start_date)
                except (ValueError, TypeError):
                    # If not ISO format or None, use current date
                    logger.info(f"Invalid start_date format: {start_date}, using current date")
                    start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
                
                if end_date:
                    try:
                        # Try to parse as ISO format
                        datetime.fromisoformat(end_date)
                    except ValueError:
                        # If not ISO format, use start_date + 7 days
                        logger.info(f"Invalid end_date format: {end_date}, using start_date + 7 days")
                        end_date = (datetime.fromisoformat(start_date) + timedelta(days=7)).isoformat()
                
                slots_result = await self.calendar_scheduler.get_available_slots(start_date, end_date)
                result = slots_result
                
            elif function_name == "schedule_appointment":
                # Update customer data with appointment details
                self.customer_data.appointment_type = parameters.get("appointment_type")
                self.customer_data.appointment_time = parameters.get("appointment_time")
                
                # Update in global dictionary
                if self.session_id in customer_data_store:
                    customer_data_dict = customer_data_store[self.session_id]
                    customer_data_dict["appointment_type"] = self.customer_data.appointment_type
                    customer_data_dict["appointment_time"] = self.customer_data.appointment_time
                    customer_data_store[self.session_id] = customer_data_dict
                
                # Schedule the appointment
                appointment_result = await self.calendar_scheduler.schedule_appointment(self.customer_data)
                result = appointment_result
                
                # Emit event to update UI
                if "error" not in appointment_result:
                    socketio.emit("appointment_scheduled", {
                        "customer": self.customer_data.to_dict(),
                        "appointment": appointment_result
                    })
                
            elif function_name == "end_conversation":
                # End the conversation
                message = parameters.get("message", "Thank you for scheduling with us!")
                result = {
                    "status": "success",
                    "message": message
                }
                
                # Emit event to update UI
                socketio.emit("conversation_ended", {
                    "message": message
                })
                
                # Close the connection after a delay
                self.is_running = False
            
            else:
                result = {"error": f"Unknown function: {function_name}"}
                
        except Exception as e:
            logger.error(f"Error executing function: {e}")
            logger.error(traceback.format_exc())
            result = {"error": str(e)}
        
        # Send the function call response
        response = {
            "type": "FunctionCallResponse",
            "function_call_id": function_call_id,
            "output": json.dumps(result)
        }
        
        logger.info(f"Sending function response: {json.dumps(response)}")
        await self.ws.send(json.dumps(response))
        logger.info(f"Function response sent")
        return result

    async def receiver(self):
        try:
            self.speaker = Speaker()
            
            with self.speaker:
                async for message in self.ws:
                    if isinstance(message, str):
                        logger.info(f"Server: {message}")
                        message_json = json.loads(message)
                        message_type = message_json.get("type")
                        
                        if message_type == "UserStartedSpeaking":
                            self.speaker.stop()
                        elif message_type == "ConversationText":
                            # Emit the conversation text to the client
                            socketio.emit("conversation_update", message_json)
                            
                        elif message_type == "FunctionCallRequest":
                            function_name = message_json.get("function_name")
                            function_call_id = message_json.get("function_call_id")
                            parameters = message_json.get("input", {})
                            
                            # Handle the function call
                            await self.handle_function_call(function_name, function_call_id, parameters)
                            
                        elif message_type == "Welcome":
                            logger.info(f"Connected with session ID: {message_json.get('session_id')}")
                            
                        elif message_type == "CloseConnection":
                            logger.info("Closing connection...")
                            await self.ws.close()
                            break
                            
                    elif isinstance(message, bytes):
                        # Convert audio to base64 and emit to client
                        audio_b64 = base64.b64encode(message).decode('utf-8')
                        socketio.emit("audio_chunk", {"audio": audio_b64})
                        
                        # Also play through speaker if available
                        if PYAUDIO_AVAILABLE:
                            await self.speaker.play(message)

        except Exception as e:
            logger.error(f"Error in receiver: {e}")
            logger.error(traceback.format_exc())

    async def run(self):
        if not await self.setup():
            return

        self.is_running = True
        try:
            stream, audio = await self.start_microphone()
            await asyncio.gather(
                self.sender(),
                self.receiver(),
            )
        except Exception as e:
            logger.error(f"Error in run: {e}")
            logger.error(traceback.format_exc())
        finally:
            self.is_running = False
            self.cleanup()


class Speaker:
    def __init__(self):
        self._queue = None
        self._stream = None
        self._thread = None
        self._stop = None

    def __enter__(self):
        if not PYAUDIO_AVAILABLE:
            return self
            
        try:
            audio = pyaudio.PyAudio()
            self._stream = audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=AGENT_AUDIO_SAMPLE_RATE,
                input=False,
                output=True,
            )
            self._queue = janus.Queue()
            self._stop = threading.Event()
            self._thread = threading.Thread(
                target=_play, args=(self._queue, self._stream, self._stop), daemon=True
            )
            self._thread.start()
        except Exception as e:
            logger.error(f"Error initializing speaker: {e}")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self._stop:
            self._stop.set()
        if self._thread:
            self._thread.join()
        if self._stream:
            self._stream.close()
        self._stream = None
        self._queue = None
        self._thread = None
        self._stop = None

    async def play(self, data):
        if self._queue and hasattr(self._queue, 'async_q'):
            return await self._queue.async_q.put(data)
        return None

    def stop(self):
        if self._queue and hasattr(self._queue, 'async_q'):
            while not self._queue.async_q.empty():
                try:
                    self._queue.async_q.get_nowait()
                except Exception:
                    break


def _play(audio_out, stream, stop):
    while not stop.is_set():
        try:
            data = audio_out.sync_q.get(True, 0.05)
            stream.write(data)
        except queue.Empty:
            pass
        except Exception as e:
            logger.error(f"Error playing audio: {e}")
            break


# Global voice agent instance
voice_agent = None


def run_async_voice_agent():
    try:
        global voice_agent
        
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Create a new VoiceAgent instance with the loop if needed
        if voice_agent is None:
            voice_agent = VoiceAgent()
        
        # Set the loop in the voice agent
        voice_agent.loop = loop
        voice_agent.mic_audio_queue = asyncio.Queue()  # Create a new queue with the new loop

        try:
            # Run the voice agent
            loop.run_until_complete(voice_agent.run())
        except asyncio.CancelledError:
            logger.info("Voice agent task was cancelled")
        except Exception as e:
            logger.error(f"Error in voice agent thread: {e}")
            logger.error(traceback.format_exc())
        finally:
            # Clean up the loop
            try:
                # Cancel all running tasks
                pending = asyncio.all_tasks(loop)
                for task in pending:
                    task.cancel()

                # Allow cancelled tasks to complete
                if pending:
                    loop.run_until_complete(
                        asyncio.gather(*pending, return_exceptions=True)
                    )

                loop.run_until_complete(loop.shutdown_asyncgens())
            finally:
                loop.close()
    except Exception as e:
        logger.error(f"Error in voice agent thread setup: {e}")
        logger.error(traceback.format_exc())


# Flask routes
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/health")
def health_check():
    """Health check endpoint for Heroku"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "pyaudio_available": PYAUDIO_AVAILABLE
    })

@app.route("/api/devices", methods=["GET"])
def get_audio_devices():
    if not PYAUDIO_AVAILABLE:
        # Return mock devices if PyAudio is not available
        return jsonify({
            "input": [
                {"index": 0, "name": "Default Microphone (Mock)", "deviceId": 0}
            ],
            "output": [
                {"index": 0, "name": "Default Speaker (Mock)", "deviceId": 0}
            ],
            "mock": True
        })
        
    try:
        p = pyaudio.PyAudio()
        input_devices = []
        output_devices = []
        
        for i in range(p.get_device_count()):
            device_info = p.get_device_info_by_index(i)
            device = {
                "index": i,
                "name": device_info.get("name"),
                "deviceId": device_info.get("deviceId", i)
            }
            
            if device_info.get("maxInputChannels") > 0:
                input_devices.append(device)
                
            if device_info.get("maxOutputChannels") > 0:
                output_devices.append(device)
                
        p.terminate()
        
        return jsonify({
            "input": input_devices,
            "output": output_devices,
            "mock": False
        })
    except Exception as e:
        logger.error(f"Error getting audio devices: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            "input": [
                {"index": 0, "name": "Default Microphone (Error)", "deviceId": 0}
            ],
            "output": [
                {"index": 0, "name": "Default Speaker (Error)", "deviceId": 0}
            ],
            "mock": True,
            "error": str(e)
        })


@socketio.on("start_voice_agent")
def handle_start_voice_agent(data=None):
    global voice_agent
    if voice_agent is None:
        voice_agent = VoiceAgent()
        if data:
            voice_agent.input_device_id = data.get("inputDeviceId")
            voice_agent.output_device_id = data.get("outputDeviceId")
        # Start the voice agent in a background thread
        socketio.start_background_task(target=run_async_voice_agent)


@socketio.on("stop_voice_agent")
def handle_stop_voice_agent():
    global voice_agent
    if voice_agent:
        voice_agent.is_running = False
        if voice_agent.loop and not voice_agent.loop.is_closed():
            try:
                # Cancel all running tasks
                for task in asyncio.all_tasks(voice_agent.loop):
                    task.cancel()
            except Exception as e:
                logger.error(f"Error stopping voice agent: {e}")
                logger.error(traceback.format_exc())
        voice_agent = None


@socketio.on("send_text")
def handle_send_text(data):
    """Handle text input from the user"""
    text = data.get("text", "")
    if text and voice_agent and voice_agent.ws:
        try:
            # Create a message to inject user text
            message = {
                "type": "InjectUserMessage",
                "message": text
            }
            # Send the message
            asyncio.run_coroutine_threadsafe(
                voice_agent.ws.send(json.dumps(message)),
                voice_agent.loop
            )
        except Exception as e:
            logger.error(f"Error sending text: {e}")
            logger.error(traceback.format_exc())


if __name__ == "__main__":
    # Get port from environment variable (Heroku sets this automatically)
    port = int(os.environ.get("PORT", 5000))
    
    # Print Python version for debugging
    print(f"Python version: {sys.version}")
    print(f"PyAudio available: {PYAUDIO_AVAILABLE}")
    
    # Check if Deepgram API key is set
    if not os.environ.get("DEEPGRAM_API_KEY"):
        print("\n" + "=" * 60)
        print("⚠️  WARNING: DEEPGRAM_API_KEY environment variable is not set!")
        print("The voice agent will not work without this key.")
        print("Please set it in your .env file or export it in your terminal.")
        print("=" * 60 + "\n")
    else:
        print("\n" + "=" * 60)
        print(f"Using Deepgram API key: {os.environ.get('DEEPGRAM_API_KEY')[:5]}...")
        print("=" * 60 + "\n")
    
    # Check if using environment variables for Google credentials
    if os.environ.get("USE_ENV_CREDENTIALS", "false").lower() == "true":
        print("\n" + "=" * 60)
        print("Using environment variables for Google Calendar credentials")
        print("=" * 60 + "\n")
    else:
        # Check if credentials.json exists
        if not os.path.exists('credentials.json'):
            print("\n" + "=" * 60)
            print("⚠️  WARNING: credentials.json file not found!")
            print("Google Calendar integration will not work without this file.")
            print("Please make sure the file exists in the project directory.")
            print("=" * 60 + "\n")
        else:
            print("\n" + "=" * 60)
            print(f"Found credentials.json file")
            print("=" * 60 + "\n")
    
    # Check if using mock calendar
    if os.environ.get("USE_MOCK_CALENDAR", "false").lower() == "true":
        print("\n" + "=" * 60)
        print("🔄 Using MOCK calendar scheduler (no Google Calendar API calls)")
        print("=" * 60 + "\n")
    
    print("\n" + "=" * 60)
    print("🚀 Voice Agent Calendar Scheduler Starting!")
    print("=" * 60)
    print(f"\nListening on port {port}")
    print("\nPress Ctrl+C to stop the server\n")
    print("=" * 60 + "\n")

    # Use eventlet for production
    socketio.run(app, host="0.0.0.0", port=port)