import os
import asyncio
import json
from datetime import datetime, timedelta
import logging
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Google Calendar API scopes
SCOPES = ['https://www.googleapis.com/auth/calendar']

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
    
    def __str__(self):
        return (
            f"Customer: {self.name}\n"
            f"Email: {self.email}\n"
            f"Phone: {self.phone}\n"
            f"ID: {self.customer_id}\n"
            f"Appointment Type: {self.appointment_type}\n"
            f"Appointment Time: {self.appointment_time}"
        )


class GoogleCalendarScheduler:
    """Class to handle Google Calendar operations"""
    
    def __init__(self, credentials_file='credentials.json', token_file='token.pickle'):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
    
    def authenticate(self):
        """Authenticate with Google Calendar API"""
        creds = None
        
        # Load existing token if available
        if os.path.exists(self.token_file):
            with open(self.token_file, 'rb') as token:
                creds = pickle.load(token)
        
        # Refresh token if expired
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        # Otherwise, get new credentials
        elif not creds:
            flow = InstalledAppFlow.from_client_secrets_file(
                self.credentials_file, SCOPES)
            creds = flow.run_local_server(port=0)
            
            # Save credentials for future use
            with open(self.token_file, 'wb') as token:
                pickle.dump(creds, token)
        
        # Build the service
        self.service = build('calendar', 'v3', credentials=creds)
        return self.service is not None
    
    async def get_available_slots(self, start_date, end_date=None, calendar_id='primary'):
        """Get available appointment slots"""
        if not self.service:
            if not self.authenticate():
                return {"error": "Failed to authenticate with Google Calendar"}
        
        if not end_date:
            end_date = (datetime.fromisoformat(start_date) + timedelta(days=7)).isoformat()
        
        # Get busy times from calendar
        body = {
            "timeMin": start_date,
            "timeMax": end_date,
            "items": [{"id": calendar_id}]
        }
        
        try:
            events_result = self.service.freebusy().query(body=body).execute()
            busy_times = events_result['calendars'][calendar_id]['busy']
            
            # Generate all possible slots (9 AM to 5 PM, 1-hour slots)
            all_slots = []
            current = datetime.fromisoformat(start_date)
            end = datetime.fromisoformat(end_date)
            
            while current <= end:
                if current.hour >= 9 and current.hour < 17:
                    slot_time = current.isoformat()
                    all_slots.append(slot_time)
                current += timedelta(hours=1)
            
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
            
            return {"available_slots": available_slots}
            
        except Exception as e:
            logger.error(f"Error getting available slots: {e}")
            return {"error": f"Failed to get available slots: {str(e)}"}
    
    async def schedule_appointment(self, customer_data, calendar_id='primary'):
        """Schedule an appointment in Google Calendar"""
        if not self.service:
            if not self.authenticate():
                return {"error": "Failed to authenticate with Google Calendar"}
        
        if not customer_data.is_valid_for_appointment():
            return {"error": "Incomplete customer data for appointment"}
        
        # Create event
        event = {
            'summary': f"{customer_data.appointment_type} with {customer_data.name}",
            'description': f"Customer ID: {customer_data.customer_id or 'N/A'}\nPhone: {customer_data.phone or 'N/A'}",
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
            return {"error": f"Failed to schedule appointment: {str(e)}"}


class CustomerDataCollector:
    """Class to collect and validate customer data"""
    
    def __init__(self):
        self.customer_data = CustomerData()
    
    async def collect_data_from_console(self):
        """Collect customer data from console input"""
        print("\n=== Customer Data Collection ===")
        
        self.customer_data.name = input("Enter customer name: ")
        self.customer_data.email = input("Enter customer email: ")
        self.customer_data.phone = input("Enter customer phone (optional): ")
        
        # Appointment type selection
        print("\nAvailable appointment types:")
        appointment_types = ["Consultation", "Follow-up", "Review", "Planning"]
        for i, apt_type in enumerate(appointment_types, 1):
            print(f"{i}. {apt_type}")
        
        type_choice = int(input("\nSelect appointment type (1-4): "))
        if 1 <= type_choice <= 4:
            self.customer_data.appointment_type = appointment_types[type_choice-1]
        else:
            print("Invalid choice. Defaulting to Consultation.")
            self.customer_data.appointment_type = "Consultation"
        
        # Get available slots
        scheduler = GoogleCalendarScheduler()
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        slots_result = await scheduler.get_available_slots(today)
        
        if "error" in slots_result:
            print(f"Error getting available slots: {slots_result['error']}")
            return False
        
        available_slots = slots_result.get("available_slots", [])
        if not available_slots:
            print("No available slots found in the next 7 days.")
            return False
        
        # Display available slots
        print("\nAvailable appointment slots:")
        for i, slot in enumerate(available_slots[:10], 1):  # Show first 10 slots
            slot_dt = datetime.fromisoformat(slot)
            print(f"{i}. {slot_dt.strftime('%A, %B %d, %Y at %I:%M %p')}")
        
        slot_choice = int(input("\nSelect appointment slot (1-10): "))
        if 1 <= slot_choice <= min(10, len(available_slots)):
            self.customer_data.appointment_time = available_slots[slot_choice-1]
        else:
            print("Invalid choice. Please try again.")
            return False
        
        # Display collected data
        print("\n=== Collected Customer Data ===")
        print(self.customer_data)
        
        confirm = input("\nConfirm appointment (y/n): ").lower()
        return confirm == 'y'
    
    def get_customer_data(self):
        """Return the collected customer data"""
        return self.customer_data


async def main():
    """Main function to run the appointment scheduler"""
    print("=== Google Calendar Appointment Scheduler ===")
    
    # Collect customer data
    collector = CustomerDataCollector()
    if not await collector.collect_data_from_console():
        print("Appointment scheduling cancelled.")
        return
    
    customer_data = collector.get_customer_data()
    
    # Schedule appointment
    scheduler = GoogleCalendarScheduler()
    result = await scheduler.schedule_appointment(customer_data)
    
    if "error" in result:
        print(f"Error scheduling appointment: {result['error']}")
    else:
        print("\n=== Appointment Scheduled Successfully ===")
        print(f"Appointment time: {datetime.fromisoformat(customer_data.appointment_time).strftime('%A, %B %d, %Y at %I:%M %p')}")
        print(f"Calendar link: {result['event_link']}")
        print("\nAn email invitation has been sent to the customer.")


if __name__ == "__main__":
    asyncio.run(main())