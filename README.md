# 📞 Voice Agent with Twilio Integration

![Voice Agent Banner](https://user-images.githubusercontent.com/74038190/212748830-4c709398-a386-4761-84d7-9e10b98fbe6e.gif)

A powerful AI voice agent that makes outbound calls using Twilio and Deepgram's Voice Agent API to schedule real estate property viewings.

## ✨ Features

- 🤖 AI-powered voice conversations using Deepgram Voice Agent
- 📱 Make outbound calls with Twilio
- 📅 Schedule appointments in Google Calendar
- 🔄 Real-time audio processing
- 🔒 Secure WebSocket communication

## 📋 Prerequisites

- Python 3.7+
- Twilio account with a phone number
- Deepgram API key with Voice Agent capabilities
- Google Calendar API credentials (optional)
- ngrok (for local development)

## 🚀 Complete Setup Guide

### Step 1: Clone the Repository

```bash
git clone https://github.com/Amruth22/voice-agent.git
cd voice-agent
git checkout twilio-with-functions
```

### Step 2: Set Up Python Environment

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Download and Set Up ngrok

1. **Download ngrok**:
   - Visit [ngrok.com/download](https://ngrok.com/download)
   - Download the appropriate version for your operating system
   - Extract the downloaded file

2. **Set up ngrok**:
   - Create a free account at [ngrok.com](https://ngrok.com)
   - Copy your auth token from the dashboard
   - Authenticate ngrok with your token:
     ```bash
     ./ngrok authtoken YOUR_AUTH_TOKEN
     ```

### Step 4: Configure Environment Variables

1. **Create .env file**:
   ```bash
   cp .env.example .env
   ```

2. **Edit the .env file** with your credentials:
   ```
   # Deepgram API Key
   DEEPGRAM_API_KEY=your_deepgram_api_key_here

   # Twilio Credentials
   TWILIO_ACCOUNT_SID=your_account_sid_here
   TWILIO_AUTH_TOKEN=your_auth_token_here
   TWILIO_PHONE_NUMBER=your_twilio_phone_number

   # Server Configuration
   HOST=localhost
   PORT=5002
   USE_SSL=false

   # Calendar Integration
   USE_MOCK_CALENDAR=true  # Set to false to use real Google Calendar
   CUSTOMER_NAME=John Doe
   CUSTOMER_EMAIL=john.doe@example.com
   CUSTOMER_PHONE=123-456-7890
   ```

### Step 5: Set Up Twilio

1. **Sign up for Twilio**:
   - Create an account at [twilio.com](https://www.twilio.com/try-twilio)
   - Purchase a phone number with voice capabilities

2. **Get your Twilio credentials**:
   - Go to your [Twilio Console Dashboard](https://www.twilio.com/console)
   - Copy your Account SID and Auth Token to your `.env` file

   ![Twilio Console](https://twilio-cms-prod.s3.amazonaws.com/images/console-dashboard.width-800.png)

3. **Create a TwiML Bin**:
   - Navigate to [TwiML Bins](https://www.twilio.com/console/runtime/twiml-bins) in your Twilio Console
   - Click "Create new TwiML Bin"
   - Give it a friendly name like "Voice Agent Connection"
   - Paste the following TwiML (you'll update the URL later):
     ```xml
     <?xml version="1.0" encoding="UTF-8"?>
     <Response>
         <Say language="en">This call may be monitored or recorded.</Say>
         <Connect>
             <Stream url="wss://your-ngrok-url.ngrok.io/twilio" />
         </Connect>
     </Response>
     ```
   - Save the TwiML Bin
   - Copy the TwiML Bin URL (it will look like `https://handler.twilio.com/twiml/EHxxxxx`)
   - Add this URL to your `.env` file as `TWILIO_TWIML_URL`

### Step 6: Set Up Google Calendar (Optional)

> 📝 **Note**: If you set `USE_MOCK_CALENDAR=true` in your `.env` file, you can skip this step.

1. **Create Google Cloud Project**:
   - Go to the [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project
   - Enable the Google Calendar API

2. **Create OAuth Credentials**:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Select "Desktop app" as the application type
   - Download the credentials JSON file
   - Rename it to `credentials.json` and place it in the project root directory

### Step 7: Start the Server

1. **Start the Twilio WebSocket server**:
   ```bash
   # On Windows:
   start_twilio_server.bat
   # On macOS/Linux:
   ./start_twilio_server.sh
   ```

   Or run directly:
   ```bash
   python twilio_server.py
   ```

2. **Start ngrok** to expose your local server:
   ```bash
   ./ngrok http 5002
   ```

   You'll see output like this:
   
   ![ngrok output](https://ngrok.com/static/img/demo.png)

3. **Update your TwiML Bin**:
   - Copy the HTTPS URL from ngrok (e.g., `https://a1b2c3d4.ngrok.io`)
   - Go back to your TwiML Bin in the Twilio Console
   - Update the Stream URL to `wss://a1b2c3d4.ngrok.io/twilio`
   - Save the updated TwiML Bin

### Step 8: Make an Outbound Call

```bash
python twilio_client.py +1234567890
```

Replace `+1234567890` with the phone number you want to call (in E.164 format).

## 📊 How It Works

![System Architecture](https://mermaid.ink/img/pako:eNp1kk1PwzAMhv9KlBOgSf3YpGlw2A6cEBJiB8QOaRo8NdCPKE2FqvbfcbuWdgU4JX7t1_Fjp0e0VhLGOJWlkBXMXqXQBWgHM6FzLQzMQRVQGZBWOVBWKwdvYMDZXIKxGlxlYKqNBmuhNLBWxsGHMFBJWDhYCVtAZZWDGgqhLLyDEQbmQjkoYaOsA1Wr0sBKGQcfYKAQFRRQCVuCNsrBJ5RCO_gCA7nQDgqhHWyFdvANBjKhHWyEdrAU2sEPGMiEdrAW2sFCaAe_YCDVFn7BwJtQDt6FcvAHBt6EcvAhlIMnMPAilINnoRw8goEnoRw8COXgHgzMhHJwJ5SDWzBwLZSDK6EcXIKBc6EcnAnl4AwMnArl4EQoB8dg4FAoB4dCOTgAA_tCOdgXysEeGNgVysGOUA62wcCWUA42hXKwAQbWhXKwJpSDVTCwIpSDZaEcLIGBRaEcLAjlYB4MzAnlYFYoB-NgYEYoB9NCORgFA1NCORgXysEIGBgWysGQUA4GwcCAUA76hXLQBwZ6hXLQI5SDbjDQJZSDTqEctIOBNqEctArloBUMNAvloEkoB41goEEoB_VCOagDA7VCOagRykE1GKgSykGlUA4qwEC5UA7KhHJQCgZKhHJQLJSDIjBQKJSDgFAO8sHAP9XK6Qo?type=png)

1. **Outbound Call Flow**:
   - The Twilio client initiates a call to the target phone number
   - When answered, Twilio connects to your WebSocket server via ngrok
   - Your server establishes a connection with Deepgram Voice Agent
   - Audio flows bidirectionally between the call and the AI agent

2. **Audio Processing**:
   - Twilio sends audio in mulaw 8kHz format
   - Your server buffers and forwards this audio to Deepgram
   - Deepgram processes the audio and generates responses
   - Your server forwards Deepgram's responses back to the call

3. **Appointment Scheduling**:
   - The AI agent collects information from the caller
   - When ready to check availability, it calls the `check_availability` function
   - Your server queries Google Calendar (or mock calendar) for available slots
   - When the caller confirms a time, the agent calls `schedule_appointment`
   - Your server creates the calendar event and confirms the booking

## 🔧 Troubleshooting

### Connection Issues

- **Twilio can't connect to your server**:
  - Ensure ngrok is running and the URL in your TwiML Bin is correct
  - Check that your server is running on the port you specified
  - Verify there are no firewalls blocking the connection

- **Server can't connect to Deepgram**:
  - Verify your Deepgram API key is correct
  - Check your internet connection
  - Look for error messages in the server logs

### Audio Issues

- **No audio from the AI agent**:
  - Check that your Deepgram API key has Voice Agent capabilities
  - Verify the audio format settings in the server configuration
  - Look for error messages related to audio processing

### Calendar Issues

- **Can't authenticate with Google Calendar**:
  - Ensure your `credentials.json` file is correctly formatted
  - Run the server once to complete the OAuth flow
  - Check that your Google Cloud project has the Calendar API enabled

## 📚 Additional Resources

- [Twilio API Documentation](https://www.twilio.com/docs/voice)
- [Deepgram Voice Agent Documentation](https://developers.deepgram.com/docs/voice-agent-api)
- [Google Calendar API Documentation](https://developers.google.com/calendar)
- [ngrok Documentation](https://ngrok.com/docs)

## 📄 License

MIT