# Twilio Integration with Google Calendar Functions

This guide explains how to use the enhanced Twilio integration that includes Google Calendar scheduling capabilities.

## Overview

This integration combines:
1. **Twilio's Voice API**: For handling phone calls
2. **Deepgram's Voice Agent API**: For natural language understanding and speech synthesis
3. **Google Calendar API**: For checking availability and scheduling appointments

The system allows callers to interact with an AI voice agent that can schedule real appointments in Google Calendar.

## Prerequisites

- A Twilio account with a phone number
- A Deepgram API key with Voice Agent capabilities
- Google Calendar API credentials (or use mock calendar mode)
- ngrok (for local development) or a publicly accessible server
- Python 3.7+

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy the `.env.example` file to `.env` and update the values:

```bash
cp .env.example .env
```

Edit the `.env` file with your actual credentials:

```
# Deepgram API Key
DEEPGRAM_API_KEY=your_deepgram_api_key_here

# Twilio Credentials
TWILIO_ACCOUNT_SID=your_account_sid_here
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE_NUMBER=your_twilio_phone_number

# TwiML URL for outbound calls
TWILIO_TWIML_URL=https://handler.twilio.com/twiml/your_twiml_bin_id

# Server Configuration
HOST=localhost
PORT=5000
USE_SSL=false

# Google Calendar Configuration
USE_MOCK_CALENDAR=true  # Set to false to use real Google Calendar
CUSTOMER_NAME=John Doe
CUSTOMER_EMAIL=john.doe@example.com
```

### 3. Set Up Google Calendar (Optional)

If you want to use real Google Calendar integration:

1. Set `USE_MOCK_CALENDAR=false` in your `.env` file
2. Place your `credentials.json` file in the project root directory
3. On first run, you'll be prompted to authorize the application

### 4. Set Up TwiML Bin in Twilio

1. Log in to your [Twilio Console](https://www.twilio.com/console)
2. Navigate to Runtime → TwiML Bins
3. Create a new TwiML Bin with the following content (replace the URL with your server's URL):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say language="en">This call may be monitored or recorded.</Say>
    <Connect>
        <Stream url="wss://your-server-url.com/twilio" />
    </Connect>
</Response>
```

4. Save the TwiML Bin and copy its URL to your `.env` file:

```
TWILIO_TWIML_URL=https://handler.twilio.com/twiml/your_twiml_bin_id
```

### 5. Start the WebSocket Server

```bash
python twilio_server.py
```

### 6. Expose Your Server (for local development)

If you're developing locally, you'll need to expose your server to the internet using ngrok:

```bash
ngrok http 5000
```

Copy the HTTPS URL provided by ngrok and update your TwiML Bin with the WebSocket URL:

```
wss://your-ngrok-url.ngrok.io/twilio
```

### 7. Make an Outbound Call

```bash
python twilio_client.py +1234567890
```

Replace `+1234567890` with the phone number you want to call.

## Function Calling Capabilities

The voice agent can perform the following functions during a call:

### 1. Get Customer Information

The agent can collect and store customer information:
- Name
- Email address
- Phone number

### 2. Check Calendar Availability

The agent can check available appointment slots in Google Calendar:
- Specify a date range
- Get a list of available time slots

### 3. Schedule Appointments

The agent can create calendar events:
- Schedule appointments at specific times
- Send email invitations to customers
- Create proper calendar events with all details

### 4. End Conversation

The agent can properly end the conversation with a farewell message.

## How It Works

1. When a call is initiated, Twilio connects to your WebSocket server
2. The server establishes a connection with Deepgram Voice Agent
3. Audio from the caller is forwarded to Deepgram for processing
4. When the agent needs to check availability or schedule an appointment, it makes a function call
5. Your server handles the function call by interacting with Google Calendar
6. The results are sent back to the agent, which formulates a natural response
7. The agent's response is forwarded back to the caller

## Heartbeat Mechanism

To prevent WebSocket timeouts, the server implements a heartbeat mechanism:
- Sends silent audio frames to Deepgram every 5 seconds when no user audio is detected
- Tracks the last time audio was sent to determine when heartbeats are needed
- Ensures the connection remains stable during periods of silence

## Troubleshooting

### Connection Issues

- Ensure your WebSocket server is accessible from the internet
- Verify that your TwiML Bin URL is correct and points to your server
- Check that your Twilio credentials are valid

### Google Calendar Issues

- Verify that your `credentials.json` file is valid
- Check that you've completed the OAuth flow
- Try using mock calendar mode (`USE_MOCK_CALENDAR=true`) for testing

### Audio Issues

- Make sure the audio encoding and sample rate match Twilio's requirements (mulaw, 8000 Hz)
- Check for any errors in the server logs

## License

MIT