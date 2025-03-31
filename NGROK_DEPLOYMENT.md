# Voice Agent with Ngrok Deployment

This guide explains how to deploy the Voice Agent application using Ngrok to expose your local development environment to the internet with full functionality.

## Why Use Ngrok?

Unlike serverless platforms like Heroku, Ngrok allows you to:
- Maintain full audio functionality (microphone input and speaker output)
- Support WebSocket connections for real-time communication
- Use all system dependencies without limitations
- Demonstrate the application with all features intact

## Prerequisites

1. Python 3.9+ installed on your local machine
2. [Ngrok](https://ngrok.com/) account and CLI installed
3. System dependencies for PyAudio:
   - **Windows**: No additional dependencies needed
   - **macOS**: `brew install portaudio`
   - **Linux**: `sudo apt-get install python3-pyaudio portaudio19-dev`
4. Deepgram API key with Voice Agent capabilities
5. Google Calendar API credentials (optional, can use mock calendar)

## Setup Instructions

### 1. Clone and Set Up the Repository

```bash
# Clone the repository
git clone https://github.com/Amruth22/voice-agent.git
cd voice-agent

# Check out the ngrok-deployment branch
git checkout ngrok-deployment

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

### 2. Configure Environment Variables

Create a `.env` file in the project root with the following variables:

```
DEEPGRAM_API_KEY=your_deepgram_api_key_here
USE_MOCK_CALENDAR=true  # Set to false to use real Google Calendar

# Optional: Customer information defaults
CUSTOMER_NAME=John Doe
CUSTOMER_EMAIL=john.doe@example.com
```

If you want to use real Google Calendar integration, you'll need to:
1. Place your `credentials.json` file in the project root
2. Set `USE_MOCK_CALENDAR=false` in your `.env` file

### 3. Run the Application Locally

```bash
python app.py
```

This will start the Flask server on port 5000 (by default).

### 4. Start Ngrok Tunnel

In a new terminal window, run:

```bash
ngrok http 5000
```

Ngrok will provide a public URL (like `https://abc123def456.ngrok.io`) that forwards to your local server.

### 5. Access Your Application

Open the Ngrok URL in your web browser. You should see the Voice Agent interface with full functionality, including:
- Voice recognition
- Real-time audio streaming
- WebSocket connections
- Calendar integration

## Troubleshooting

### Audio Issues

If you encounter audio issues:

1. **Browser Permissions**: Make sure you've granted microphone permissions to the Ngrok URL
2. **HTTPS**: Ensure you're using the HTTPS Ngrok URL, as browsers require secure connections for microphone access
3. **PyAudio Installation**: Verify PyAudio is correctly installed with `pip list | grep pyaudio`

### WebSocket Connection Issues

If WebSocket connections fail:

1. **Check Ngrok Logs**: Look for connection errors in the Ngrok terminal
2. **Browser Console**: Check for WebSocket errors in your browser's developer console
3. **Firewall**: Ensure your firewall isn't blocking WebSocket connections

### Google Calendar Integration

If calendar integration isn't working:

1. **Credentials**: Verify your `credentials.json` file is in the project root
2. **OAuth Consent**: The first time you use Google Calendar, you'll need to complete the OAuth consent flow
3. **Mock Calendar**: Try using the mock calendar (`USE_MOCK_CALENDAR=true`) to test other functionality

## Limitations

1. **Temporary URLs**: Free Ngrok accounts provide URLs that change each time you restart Ngrok
2. **Session Duration**: Free Ngrok sessions last 2 hours before requiring a restart
3. **Bandwidth Limits**: Free accounts have limited bandwidth
4. **Requires Local Machine**: Your computer must remain running for the application to be accessible

## Upgrading to Ngrok Pro

For production or extended demonstrations, consider upgrading to Ngrok Pro for:
- Reserved domains (fixed URLs)
- Longer session durations
- Higher bandwidth limits
- Additional features like IP restrictions and custom domains

## License

MIT