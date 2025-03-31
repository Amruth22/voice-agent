import os
from twilio.rest import Client
from dotenv import load_dotenv
import argparse
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

def make_call(to_number, from_number=None, twiml_url=None):
    """
    Make an outbound call using Twilio
    
    Args:
        to_number (str): The phone number to call (E.164 format)
        from_number (str, optional): The Twilio phone number to use (E.164 format)
        twiml_url (str, optional): The URL of the TwiML Bin to use
        
    Returns:
        str: The SID of the created call
    """
    # Get credentials from environment variables
    account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
    
    # Use default from_number if not provided
    if not from_number:
        from_number = os.environ.get("TWILIO_PHONE_NUMBER")
    
    # Use default TwiML URL if not provided
    if not twiml_url:
        twiml_url = os.environ.get("TWILIO_TWIML_URL")
    
    # Validate required parameters
    if not account_sid or not auth_token:
        raise ValueError("TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN must be set in environment variables")
    
    if not from_number:
        raise ValueError("From phone number must be provided either as an argument or in TWILIO_PHONE_NUMBER environment variable")
    
    if not twiml_url:
        raise ValueError("TwiML URL must be provided either as an argument or in TWILIO_TWIML_URL environment variable")
    
    # Initialize Twilio client
    client = Client(account_sid, auth_token)
    
    # Make the call
    logger.info(f"Making call from {from_number} to {to_number} using TwiML URL: {twiml_url}")
    call = client.calls.create(
        url=twiml_url,
        to=to_number,
        from_=from_number
    )
    
    logger.info(f"Call initiated with SID: {call.sid}")
    return call.sid

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Make an outbound call using Twilio")
    parser.add_argument("to_number", help="The phone number to call (E.164 format)")
    parser.add_argument("--from-number", help="The Twilio phone number to use (E.164 format)")
    parser.add_argument("--twiml-url", help="The URL of the TwiML Bin to use")
    
    args = parser.parse_args()
    
    try:
        call_sid = make_call(args.to_number, args.from_number, args.twiml_url)
        print(f"Call initiated with SID: {call_sid}")
    except Exception as e:
        logger.error(f"Error making call: {e}")
        exit(1)