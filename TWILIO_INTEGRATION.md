# Twilio Integration with Deepgram Voice Agent

This guide explains how to integrate Twilio with Deepgram Voice Agent to create an interactive voice response (IVR) system that can handle phone calls using AI.

## Overview

The integration consists of two main components:

1. **Twilio WebSocket Server**: A server that handles WebSocket connections from Twilio and forwards audio to/from Deepgram Voice Agent.
2. **Twilio Client**: A script for making outbound calls using Twilio.

## Prerequisites

- A Twilio account with a phone number
- A Deepgram API key with Voice Agent capabilities
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
DEEPGRAM_API_KEY=your_deepgram_api_key_here
TWILIO_ACCOUNT_SID=your_account_sid_here
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE_NUMBER=your_twilio_phone_number
```

### 3. Set Up TwiML Bin in Twilio

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

### 4. Start the WebSocket Server

```bash
python twilio_server.py
```

### 5. Expose Your Server (for local development)

If you're developing locally, you'll need to expose your server to the internet using ngrok:

```bash
ngrok http 5000
```

Copy the HTTPS URL provided by ngrok and update your TwiML Bin with the WebSocket URL:

```
wss://your-ngrok-url.ngrok.io/twilio
```

### 6. Make an Outbound Call

```bash
python twilio_client.py +1234567890
```

Replace `+1234567890` with the phone number you want to call.

## How It Works

1. When a call is initiated, Twilio connects to your WebSocket server
2. The server establishes a connection with Deepgram Voice Agent
3. Audio from the caller is forwarded to Deepgram for processing
4. Deepgram's responses are forwarded back to the caller
5. The conversation flows naturally between the caller and the AI agent

## Customizing the Voice Agent

You can customize the behavior of the Voice Agent by modifying the `PROMPT_TEMPLATE` in `twilio_server.py`. This template provides instructions to the AI about how to respond to callers.

## Troubleshooting

### Connection Issues

- Ensure your WebSocket server is accessible from the internet
- Verify that your TwiML Bin URL is correct and points to your server
- Check that your Twilio credentials are valid

### Audio Issues

- Make sure the audio encoding and sample rate match Twilio's requirements (mulaw, 8000 Hz)
- Check for any errors in the server logs

### Deepgram API Issues

- Verify that your Deepgram API key is valid and has Voice Agent capabilities
- Check the server logs for any error messages from Deepgram

## Advanced Configuration

### SSL Configuration

For production deployments, you should use SSL:

1. Set `USE_SSL=true` in your `.env` file
2. Provide paths to your SSL certificate and key:
   ```
   SSL_CERT=path/to/cert.pem
   SSL_KEY=path/to/key.pem
   ```
3. Update your TwiML Bin URL to use `wss://` instead of `ws://`

### Custom Voice and Models

You can customize the voice and models used by Deepgram by setting these environment variables:

```
DEEPGRAM_VOICE=aura-asteria-en
DEEPGRAM_LISTEN_MODEL=nova-2
DEEPGRAM_THINK_MODEL=gpt-4o-mini
DEEPGRAM_THINK_PROVIDER=open_ai
```

## License

MIT