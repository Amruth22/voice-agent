from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO
import os
import asyncio
import json
import logging
import threading
import queue
import time
from datetime import datetime, timedelta
import pyaudio
import janus
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

# Template for the prompt that will be formatted with current date
PROMPT_TEMPLATE = """You are a friendly and professional appointment scheduler. Your role is to assist customers in scheduling appointments in Google Calendar.

CURRENT DATE AND TIME CONTEXT:
Today is {current_date}. Use this as context when discussing appointments. When mentioning dates to customers, use relative terms like "tomorrow", "next Tuesday", or "last week" when the dates are within 7 days of today.

PERSONALITY & TONE:
- Be warm, professional, and conversational
- Use natural, flowing speech (avoid bullet points or listing)
- Show empathy and patience
- Collect all necessary information for scheduling an appointment

INFORMATION TO COLLECT:
- Customer name
- Customer email (required for calendar invitation)
- Customer phone number (optional)
- Appointment type (Consultation, Follow-up, Review, Planning)
- Preferred date and time for the appointment

FUNCTION RESPONSES:
When receiving function results, format responses naturally:

1. For available slots:
   - "I have a few openings next week. Would you prefer Tuesday at 2 PM or Wednesday at 3 PM?"

2. For appointment confirmation:
   - "Great! I've scheduled your [appointment type] for [date] at [time]. You'll receive an email confirmation shortly."

3. For errors:
   - Never expose technical details
   - Say something like "I'm having trouble accessing the calendar right now" or "Could you please try again?"

EXAMPLES OF GOOD RESPONSES:
✓ "I'd be happy to schedule an appointment for you. Could I get your name and email address?"
✓ "I see you'd like a consultation. Let me check what times are available next week."
✓ "I've found a few available slots. Would Tuesday at 2 PM work for you?"

FILLER PHRASES:
When you need to indicate you're looking something up, use phrases like:
- "Let me check the calendar for available slots..."
- "One moment while I schedule that appointment..."
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


# Google Calendar Scheduler
class GoogleCalendarScheduler:
    """Class to handle Google Calendar operations"""
    
    def __init__(self, credentials_file='credentials.json', token_file='token.pickle'):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
    
    def authenticate(self):
        """Authenticate with Google Calendar API"""
        try:
            logger.info(f"Authenticating with Google Calendar API")
            logger.info(f"Credentials file: {self.credentials_file}, exists: {os.path.exists(self.credentials_file)}")
            logger.info(f"Token file: {self.token_file}, exists: {os.path.exists(self.token_file)}")
            
            creds = None
            
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
            # Otherwise, get new credentials
            elif not creds:
                logger.info("No token found, getting new credentials")
                if not os.path.exists(self.credentials_file):
                    logger.error(f"Credentials file not found: {self.credentials_file}")
                    return False
                    
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, SCOPES)
                creds = flow.run_local_server(port=0)
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
            end_date = (datetime.fromisoformat(start_date) + timedelta(days=7)).isoformat()
            logger.info(f"End date not provided, using {end_date}")
        
        # Get busy times from calendar
        body = {
            "timeMin": start_date,
            "timeMax": end_date,
            "items": [{"id": calendar_id}]
        }
        
        try:
            logger.info(f"Querying freebusy with body: {body}")
            events_result = self.service.freebusy().query(body=body).execute()
            busy_times = events_result['calendars'][calendar_id]['busy']
            logger.info(f"Found {len(busy_times)} busy times")
            
            # Generate all possible slots (9 AM to 5 PM, 1-hour slots)
            all_slots = []
            current = datetime.fromisoformat(start_date)
            end = datetime.fromisoformat(end_date)
            
            while current <= end:
                if current.hour >= 9 and current.hour < 17:
                    slot_time = current.isoformat()
                    all_slots.append(slot_time)
                current += timedelta(hours=1)
            
            logger.info(f"Generated {len(all_slots)} possible slots")
            
            # Filter out busy slots
            available_slots = []
            for slot in all_slots:
                slot_dt = datetime.fromisoformat(slot)
                slot_end = (slot_dt + timedelta(hours=1)).isoformat()
                
                is_available = True
                for busy in busy_times:
                    busy_start = datetime.fromisoformat(busy['start'].replace('Z', '+00:00'))
                    busy_end = datetime.fromisoformat(busy['end'].replace('Z', '+00:00'))
                    
                    if (slot_dt >= busy_start and slot_dt < busy_end) or \
                       (slot_dt < busy_start and datetime.fromisoformat(slot_end) > busy_start):
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
        
        # Create event
        event = {
            'summary': f"{customer_data.appointment_type} with {customer_data.name}",
            'description': f"Phone: {customer_data.phone or 'N/A'}",
            'start': {
                'dateTime': customer_data.appointment_time,
                'timeZone': 'America/New_York',  # Adjust timezone as needed
            },
            'end': {
                'dateTime': (datetime.fromisoformat(customer_data.appointment_time) + timedelta(hours=1)).isoformat(),
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


# Voice Agent class
class VoiceAgent:
    def __init__(self):
        self.mic_audio_queue = asyncio.Queue()
        self.speaker = None
        self.ws = None
        self.is_running = False
        self.loop = None
        self.audio = None
        self.stream = None
        self.input_device_id = None
        self.output_device_id = None
        self.customer_data = CustomerData()
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
            formatted_prompt = PROMPT_TEMPLATE.format(current_date=current_date)
            
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
                            "content": "Hello! I'm your appointment scheduling assistant. How can I help you today?",
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
                raise Exception("No input device found")

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
            raise

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
                
                # Store in session
                session["customer_data"] = self.customer_data.to_dict()
                
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
                
                # Update session
                session["customer_data"] = self.customer_data.to_dict()
                
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
                        
                        # Also play through speaker
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

    def __exit__(self, exc_type, exc_value, traceback):
        self._stop.set()
        self._thread.join()
        self._stream.close()
        self._stream = None
        self._queue = None
        self._thread = None
        self._stop = None

    async def play(self, data):
        return await self._queue.async_q.put(data)

    def stop(self):
        if self._queue and self._queue.async_q:
            while not self._queue.async_q.empty():
                try:
                    self._queue.async_q.get_nowait()
                except janus.QueueEmpty:
                    break


def _play(audio_out, stream, stop):
    while not stop.is_set():
        try:
            data = audio_out.sync_q.get(True, 0.05)
            stream.write(data)
        except queue.Empty:
            pass


# Global voice agent instance
voice_agent = None


def run_async_voice_agent():
    try:
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Set the loop in the voice agent
        voice_agent.set_loop(loop)

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


@app.route("/api/devices", methods=["GET"])
def get_audio_devices():
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
            "output": output_devices
        })
    except Exception as e:
        logger.error(f"Error getting audio devices: {e}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


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
    # Print Python version for debugging
    print(f"Python version: {sys.version}")
    
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
    
    print("\n" + "=" * 60)
    print("🚀 Voice Agent Calendar Scheduler Starting!")
    print("=" * 60)
    print("\n1. Open this link in your browser to start the demo:")
    print("   http://127.0.0.1:5000")
    print("\n2. Click 'Start Voice Agent' when the page loads")
    print("\n3. Speak with the agent using your microphone or type in the text box")
    print("\nPress Ctrl+C to stop the server\n")
    print("=" * 60 + "\n")

    socketio.run(app, debug=True)