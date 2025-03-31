import asyncio
import base64
import json
import sys
import websockets
import ssl
import os
from dotenv import load_dotenv
import logging
import traceback
from datetime import datetime, timedelta, timezone
import pickle
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import secrets
import time

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get Deepgram API key from environment variables
DEEPGRAM_API_KEY = os.environ.get("DEEPGRAM_API_KEY")
if not DEEPGRAM_API_KEY:
    logger.error("DEEPGRAM_API_KEY environment variable is not set!")
    sys.exit(1)

# Voice agent settings
VOICE = os.environ.get("DEEPGRAM_VOICE", "aura-asteria-en")
LISTEN_MODEL = os.environ.get("DEEPGRAM_LISTEN_MODEL", "nova-2")
THINK_MODEL = os.environ.get("DEEPGRAM_THINK_MODEL", "gpt-4o-mini")
THINK_PROVIDER = os.environ.get("DEEPGRAM_THINK_PROVIDER", "open_ai")

# Google Calendar API scopes
SCOPES = ['https://www.googleapis.com/auth/calendar']

# Customer information (can be overridden in .env)
name = os.environ.get("CUSTOMER_NAME", "Customer")
email = os.environ.get("CUSTOMER_EMAIL", "customer@example.com")
phone_number= os.environ.get("CUSTOMER_PHONE", "123-456-7890")
# Template for the prompt that will be formatted with current date
PROMPT_TEMPLATE = """You are a friendly and professional real estate appointment scheduler for Premium Properties. Your role is to proactively call potential buyers to schedule property viewings in Google Calendar.

CURRENT DATE AND TIME CONTEXT: 
Today is {current_date}. Use this as context when discussing appointments. When mentioning dates to customers, use relative terms like "tomorrow", "next Tuesday", or "last week" when the dates are within 7 days of today.

CUSTOMER INFORMATION: 
You are calling a customer named {name}, whose phone number is {phone_number} and email is {email}. Use this information appropriately during the call.

PERSONALITY & TONE:
- Be warm, professional, and conversational
- Use natural, flowing speech (avoid bullet points or listing)
- Show empathy and patience
- Sound enthusiastic about the property
- Acknowledge you're the one calling them

OUTBOUND CALL FLOW:
1. Begin with the welcome message
2. Immediately clarify: "I'm calling from Premium Properties regarding your interest in our luxury properties."
3. Mention specific property: "I wanted to tell you about our [specific property] that matches what you're looking for."
4. Ask if they're interested in viewing: "Would you be interested in scheduling a viewing of this property?"
5. If interested, check purchase intent: "May I ask if you're considering this as a potential purchase?"
6. Only if they express buying interest, proceed to scheduling
7. Offer specific time slots: "I have availability this Thursday at 2 PM or Friday at 11 AM."
8. After customer indicates a preferred time, explicitly confirm: "So you're available on [chosen date] at [chosen time]? Can I proceed with booking this time slot for you?"
9. Only after explicit confirmation, finalize the appointment

INFORMATION TO COLLECT:
- Confirmation of interest in the specific property
- Verification of purchase intent
- Preferred date and time for viewing
- Explicit confirmation of the chosen time slot before booking
- Any specific questions they have about the property before the viewing

HANDLING COMMON RESPONSES:
- If customer is surprised by the call: "I apologize for calling unexpectedly. You expressed interest in our properties, so I wanted to follow up personally."
- If customer is busy: "I understand. When would be a better time to call back?"
- If customer requests more information: "I'd be happy to email you the property details right away."

APPOINTMENT CONFIRMATION:
"Excellent! I've scheduled your property viewing for [date] at [time]. You'll receive a confirmation email shortly at {email}. Is there anything specific you'd like to know about the property before your visit?"

CALL CLOSING:
"Thank you for your time today, {name}. We look forward to showing you the property on [date]. If you have any questions before then, please don't hesitate to call us back at [office_phone]. Have a wonderful day!"
"""

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

def sts_connect():
    """Connect to Deepgram Voice Agent API"""
    sts_ws = websockets.connect(
        "wss://agent.deepgram.com/agent", 
        subprotocols=["token", DEEPGRAM_API_KEY]
    )
    return sts_ws

async def twilio_handler(twilio_ws):
    """Handle Twilio WebSocket connection"""
    logger.info("Twilio handler started")
    audio_queue = asyncio.Queue()
    streamsid_queue = asyncio.Queue()
    
    # Create a session ID and customer data instance
    session_id = secrets.token_hex(8)
    customer_data = CustomerData()
    
    # Use mock scheduler if USE_MOCK_CALENDAR is set to True
    use_mock = os.environ.get("USE_MOCK_CALENDAR", "false").lower() == "true"
    if use_mock:
        logger.info("Using mock calendar scheduler")
        calendar_scheduler = MockCalendarScheduler()
    else:
        logger.info("Using Google Calendar scheduler")
        calendar_scheduler = GoogleCalendarScheduler()

    async with sts_connect() as sts_ws:
        # Format the prompt with the current date
        current_date = datetime.now().strftime("%A, %B %d, %Y")
        formatted_prompt = PROMPT_TEMPLATE.format(current_date=current_date,name=name,email=email,phone_number=phone_number)
        
        # Configure Deepgram Voice Agent
        config_message = {
            "type": "SettingsConfiguration",
            "audio": {
                "input": {
                    "encoding": "mulaw",
                    "sample_rate": 8000,
                },
                "output": {
                    "encoding": "mulaw",
                    "sample_rate": 8000,
                    "container": "none",
                },
            },
            "agent": {
                "listen": {"model": LISTEN_MODEL},
                "think": {
                    "provider": {"type": THINK_PROVIDER},
                    "model": THINK_MODEL,
                    "instructions": formatted_prompt,
                    "functions": FUNCTION_DEFINITIONS,
                },
                "speak": {"model": VOICE},
            },
            "context": {
                "messages": [
                    {
                        "role": "assistant",
                        "content": f"Hello {name}! This is Priya calling from Premium Properties. I'm your appointment scheduling assistant. I hope I'm not catching you at a bad time?",
                    }
                ],
                "replay": True,
            },
        }

        logger.info("Sending configuration to Deepgram")
        await sts_ws.send(json.dumps(config_message))
        
        # Wait for settings applied confirmation
        response = await sts_ws.recv()
        response_json = json.loads(response)
        if response_json.get("type") == "SettingsApplied":
            logger.info("Settings applied successfully")
        else:
            logger.info(f"Received response: {response_json}")

        async def sts_sender(sts_ws):
            """Send audio from Twilio to Deepgram"""
            logger.info("sts_sender started")
            while True:
                try:
                    # Get audio data from queue
                    chunk = await audio_queue.get()
                    await sts_ws.send(chunk)
                except Exception as e:
                    logger.error(f"Error in sts_sender: {e}")
                    break

        async def handle_function_call(function_name, function_call_id, parameters):
            """Handle function calls from the voice agent"""
            logger.info(f"Function call received: {function_name}")
            logger.info(f"Parameters: {parameters}")
            
            result = {}
            
            try:
                if function_name == "get_customer_info":
                    # Store customer info
                    customer_data.name = parameters.get("name")
                    customer_data.email = parameters.get("email")
                    customer_data.phone = parameters.get("phone")
                    
                    # Store in global dictionary
                    customer_data_store[session_id] = customer_data.to_dict()
                    
                    result = {
                        "status": "success",
                        "message": f"Customer information stored for {customer_data.name}"
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
                    
                    slots_result = await calendar_scheduler.get_available_slots(start_date, end_date)
                    result = slots_result
                    
                elif function_name == "schedule_appointment":
                    # Update customer data with appointment details
                    customer_data.appointment_type = parameters.get("appointment_type")
                    customer_data.appointment_time = parameters.get("appointment_time")
                    
                    # Update in global dictionary
                    if session_id in customer_data_store:
                        customer_data_dict = customer_data_store[session_id]
                        customer_data_dict["appointment_type"] = customer_data.appointment_type
                        customer_data_dict["appointment_time"] = customer_data.appointment_time
                        customer_data_store[session_id] = customer_data_dict
                    
                    # Schedule the appointment
                    appointment_result = await calendar_scheduler.schedule_appointment(customer_data)
                    result = appointment_result
                    
                elif function_name == "end_conversation":
                    # End the conversation
                    message = parameters.get("message", "Thank you for scheduling with us!")
                    result = {
                        "status": "success",
                        "message": message
                    }
                    
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
            await sts_ws.send(json.dumps(response))
            logger.info(f"Function response sent")
            return result

        async def sts_receiver(sts_ws):
            """Receive responses from Deepgram and forward to Twilio"""
            logger.info("sts_receiver started")
            # Wait until the Twilio WS connection provides the streamSid
            streamsid = await streamsid_queue.get()
            logger.info(f"Got stream SID: {streamsid}")
            
            # For each message received from Deepgram, forward it to the call
            async for message in sts_ws:
                if isinstance(message, str):
                    logger.info(f"Text message from Deepgram: {message}")
                    # Handle different message types
                    try:
                        decoded = json.loads(message)
                        message_type = decoded.get('type')
                        
                        if message_type == 'UserStartedSpeaking':
                            logger.info("User started speaking, sending clear message to Twilio")
                            clear_message = {
                                "event": "clear",
                                "streamSid": streamsid
                            }
                            await twilio_ws.send(json.dumps(clear_message))
                        elif message_type == "FunctionCallRequest":
                            function_name = decoded.get("function_name")
                            function_call_id = decoded.get("function_call_id")
                            parameters = decoded.get("input", {})
                            
                            # Handle the function call
                            await handle_function_call(function_name, function_call_id, parameters)
                    except json.JSONDecodeError:
                        logger.error(f"Failed to decode JSON message: {message}")
                    continue

                # Handle binary audio data
                logger.debug(f"Received binary audio from Deepgram: {len(message)} bytes")
                raw_mulaw = message

                # Construct a Twilio media message with the raw mulaw
                media_message = {
                    "event": "media",
                    "streamSid": streamsid,
                    "media": {"payload": base64.b64encode(raw_mulaw).decode("ascii")},
                }

                # Send the TTS audio to the attached phone call
                await twilio_ws.send(json.dumps(media_message))

        async def twilio_receiver(twilio_ws):
            """Receive audio from Twilio and forward to Deepgram"""
            logger.info("twilio_receiver started")
            # Twilio sends audio data as 160 byte messages containing 20ms of audio each
            # Buffer 20 Twilio messages (0.4 seconds of audio) to improve throughput
            BUFFER_SIZE = 20 * 160

            inbuffer = bytearray(b"")
            async for message in twilio_ws:
                try:
                    data = json.loads(message)
                    if data["event"] == "start":
                        logger.info("Got stream SID from Twilio")
                        start = data["start"]
                        streamsid = start["streamSid"]
                        streamsid_queue.put_nowait(streamsid)
                    elif data["event"] == "connected":
                        logger.info("Twilio connected event received")
                        continue
                    elif data["event"] == "media":
                        media = data["media"]
                        chunk = base64.b64decode(media["payload"])
                        if media["track"] == "inbound":
                            inbuffer.extend(chunk)
                    elif data["event"] == "stop":
                        logger.info("Twilio stop event received")
                        break

                    # Check if our buffer is ready to send to the audio queue
                    while len(inbuffer) >= BUFFER_SIZE:
                        chunk = inbuffer[:BUFFER_SIZE]
                        audio_queue.put_nowait(chunk)
                        inbuffer = inbuffer[BUFFER_SIZE:]
                except Exception as e:
                    logger.error(f"Error processing Twilio message: {e}")
                    break

        # Run all tasks concurrently
        await asyncio.wait(
            [
                asyncio.ensure_future(sts_sender(sts_ws)),
                asyncio.ensure_future(sts_receiver(sts_ws)),
                asyncio.ensure_future(twilio_receiver(twilio_ws)),
            ]
        )
            
        await twilio_ws.close()

async def router(websocket, path):
    """Route incoming WebSocket connections based on path"""
    logger.info(f"Incoming connection on path: {path}")
    if path == "/twilio":
        logger.info("Starting Twilio handler")
        await twilio_handler(websocket)
    else:
        logger.warning(f"Unknown path: {path}")
        await websocket.close(1008, f"Unknown path: {path}")

def main():
    """Main function to start the WebSocket server"""
    # Check if SSL is enabled
    use_ssl = os.environ.get("USE_SSL", "false").lower() == "true"
    host = os.environ.get("HOST", "localhost")
    port = int(os.environ.get("PORT", 5002))
    
    if use_ssl:
        # SSL configuration
        ssl_cert = os.environ.get("SSL_CERT", "cert.pem")
        ssl_key = os.environ.get("SSL_KEY", "key.pem")
        
        if not os.path.exists(ssl_cert) or not os.path.exists(ssl_key):
            logger.error(f"SSL certificates not found: {ssl_cert}, {ssl_key}")
            sys.exit(1)
            
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain(ssl_cert, ssl_key)
        server = websockets.serve(router, host, port, ssl=ssl_context)
        logger.info(f"Server starting on wss://{host}:{port}")
    else:
        # Non-SSL configuration
        server = websockets.serve(router, host, port)
        logger.info(f"Server starting on ws://{host}:{port}")

    # Start the server
    asyncio.get_event_loop().run_until_complete(server)
    asyncio.get_event_loop().run_forever()

if __name__ == "__main__":
    # Check if Deepgram API key is set
    if not DEEPGRAM_API_KEY:
        print("\n" + "=" * 60)
        print("⚠️  WARNING: DEEPGRAM_API_KEY environment variable is not set!")
        print("The voice agent will not work without this key.")
        print("Please set it in your .env file or export it in your terminal.")
        print("=" * 60 + "\n")
    else:
        print("\n" + "=" * 60)
        print(f"Using Deepgram API key: {DEEPGRAM_API_KEY[:5]}...")
        print("=" * 60 + "\n")
    
    # Check if credentials.json exists
    use_mock = os.environ.get("USE_MOCK_CALENDAR", "false").lower() == "true"
    if not os.path.exists('credentials.json') and not use_mock:
        print("\n" + "=" * 60)
        print("⚠️  WARNING: credentials.json file not found!")
        print("Google Calendar integration will not work without this file.")
        print("Please make sure the file exists in the project directory or set USE_MOCK_CALENDAR=true.")
        print("=" * 60 + "\n")
    elif os.path.exists('credentials.json'):
        print("\n" + "=" * 60)
        print(f"Found credentials.json file")
        print("=" * 60 + "\n")
    
    # Check if using mock calendar
    if use_mock:
        print("\n" + "=" * 60)
        print("🔄 Using MOCK calendar scheduler (no Google Calendar API calls)")
        print("=" * 60 + "\n")
    
    print("\n" + "=" * 60)
    print("🚀 Twilio Voice Agent Calendar Scheduler Starting!")
    print("=" * 60)
    print("\n1. Make sure your TwiML Bin is configured with:")
    print("   <Connect><Stream url=\"wss://your-server-url.com/twilio\" /></Connect>")
    print("\n2. Use twilio_client.py to make outbound calls")
    print("\nPress Ctrl+C to stop the server\n")
    print("=" * 60 + "\n")
    
    sys.exit(main() or 0)