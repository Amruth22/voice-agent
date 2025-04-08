# 🌟 AI Voice Agent with Twilio Integration

<div align="center">
  <img src="https://i.imgur.com/8scBDDD.gif" alt="AI Voice Agent Banner" width="100%">
  
  <p>
    <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.7+-blue.svg?style=for-the-badge&logo=python&logoColor=white" alt="Python"></a>
    <a href="https://www.twilio.com/"><img src="https://img.shields.io/badge/Powered%20by-Twilio-F22F46?style=for-the-badge&logo=twilio&logoColor=white" alt="Twilio"></a>
    <a href="https://deepgram.com/"><img src="https://img.shields.io/badge/AI%20Voice-Deepgram-7956EF?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEyIDI0QzE4LjYyNzQgMjQgMjQgMTguNjI3NCAyNCAxMkMyNCA1LjM3MjU4IDE4LjYyNzQgMCAxMiAwQzUuMzcyNTggMCAwIDUuMzcyNTggMCAxMkMwIDE4LjYyNzQgNS4zNzI1OCAyNCAxMiAyNFoiIGZpbGw9IiM3OTU2RUYiLz4KPHBhdGggZD0iTTcuNjQxMDQgMTcuMzA3OUw3LjY0MTA0IDYuNjkyMDhMMTYuMzU5IDYuNjkyMDhMMTYuMzU5IDE3LjMwNzlMNy42NDEwNCAxNy4zMDc5WiIgZmlsbD0id2hpdGUiLz4KPC9zdmc+Cg==" alt="Deepgram"></a>
    <a href="https://calendar.google.com/"><img src="https://img.shields.io/badge/Calendar-Google-4285F4?style=for-the-badge&logo=google-calendar&logoColor=white" alt="Google Calendar"></a>
  </p>
  
  <h3>Transform your customer outreach with AI-powered voice calls</h3>
  
  <p>A sophisticated AI voice agent that makes outbound calls using Twilio and Deepgram's Voice Agent API to schedule real estate property viewings with natural, human-like conversations.</p>
</div>

---

## 🔥 Features

<table>
  <tr>
    <td width="50%">
      <h3>🤖 Conversational AI</h3>
      <ul>
        <li>Natural language understanding</li>
        <li>Context-aware responses</li>
        <li>Human-like voice synthesis</li>
        <li>Customizable personality</li>
      </ul>
    </td>
    <td width="50%">
      <h3>📱 Telephony Integration</h3>
      <ul>
        <li>Outbound calling with Twilio</li>
        <li>High-quality audio processing</li>
        <li>Real-time bidirectional streaming</li>
        <li>Call monitoring capabilities</li>
      </ul>
    </td>
  </tr>
  <tr>
    <td width="50%">
      <h3>📅 Smart Scheduling</h3>
      <ul>
        <li>Google Calendar integration</li>
        <li>Availability checking</li>
        <li>Appointment creation</li>
        <li>Email confirmations</li>
      </ul>
    </td>
    <td width="50%">
      <h3>⚙️ Advanced Configuration</h3>
      <ul>
        <li>Customizable voice models</li>
        <li>Adjustable AI parameters</li>
        <li>Flexible deployment options</li>
        <li>Detailed logging</li>
      </ul>
    </td>
  </tr>
</table>

---

## 📋 Prerequisites

Before you begin, ensure you have the following:

<table>
  <tr>
    <td width="33%">
      <div align="center">
        <img src="https://i.imgur.com/Cda9UR4.png" width="100" height="100">
        <h4>Development Environment</h4>
      </div>
      <ul>
        <li>Python 3.7+</li>
        <li>pip package manager</li>
        <li>Git</li>
        <li>Command-line terminal</li>
      </ul>
    </td>
    <td width="33%">
      <div align="center">
        <img src="https://i.imgur.com/4LL82wp.png" width="100" height="100">
        <h4>API Accounts</h4>
      </div>
      <ul>
        <li>Twilio account</li>
        <li>Twilio phone number</li>
        <li>Deepgram API key</li>
        <li>Google Cloud account (optional)</li>
      </ul>
    </td>
    <td width="33%">
      <div align="center">
        <img src="https://i.imgur.com/Ql2TaV4.png" width="100" height="100">
        <h4>Network Tools</h4>
      </div>
      <ul>
        <li>ngrok</li>
        <li>Internet connection</li>
        <li>Firewall access for WebSockets</li>
        <li>Browser for OAuth (if using Google Calendar)</li>
      </ul>
    </td>
  </tr>
</table>

---

## 🚀 Complete Setup Guide

<details open>
<summary><h3>Step 1: Clone the Repository</h3></summary>

Open your terminal and run the following commands:

```bash
# Clone the repository
git clone https://github.com/Amruth22/voice-agent.git

# Navigate to the project directory
cd voice-agent

# Switch to the Twilio integration branch
git checkout twilio-with-functions
```

This will download the project code and switch to the branch with Twilio integration.

</details>

<details>
<summary><h3>Step 2: Set Up Python Environment</h3></summary>

Create and activate a virtual environment to isolate the project dependencies:

<table>
  <tr>
    <th>Windows</th>
    <th>macOS/Linux</th>
  </tr>
  <tr>
    <td>
      
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

</td>
    <td>
      
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

</td>
  </tr>
</table>

You should see `(venv)` at the beginning of your command prompt, indicating the virtual environment is active.

</details>

<details>
<summary><h3>Step 3: Download and Set Up ngrok</h3></summary>

ngrok creates a secure tunnel to expose your local server to the internet, allowing Twilio to connect to your application.

#### 3.1 Download ngrok

<table>
  <tr>
    <th>Windows</th>
    <th>macOS</th>
    <th>Linux</th>
  </tr>
  <tr>
    <td>
      <ol>
        <li>Visit <a href="https://ngrok.com/download">ngrok.com/download</a></li>
        <li>Download the Windows ZIP file</li>
        <li>Extract the ZIP file to a location of your choice</li>
      </ol>
    </td>
    <td>
      <ol>
        <li>Visit <a href="https://ngrok.com/download">ngrok.com/download</a></li>
        <li>Download the macOS ZIP file</li>
        <li>Extract the ZIP file to a location of your choice</li>
        <li>Alternatively, install with Homebrew:<br><code>brew install ngrok</code></li>
      </ol>
    </td>
    <td>
      <ol>
        <li>Visit <a href="https://ngrok.com/download">ngrok.com/download</a></li>
        <li>Download the Linux ZIP file</li>
        <li>Extract the ZIP file:<br><code>unzip /path/to/ngrok.zip</code></li>
        <li>Make it executable:<br><code>chmod +x ./ngrok</code></li>
      </ol>
    </td>
  </tr>
</table>

#### 3.2 Create ngrok Account and Get Auth Token

1. Sign up for a free account at [ngrok.com/signup](https://ngrok.com/signup)
2. After signing in, navigate to the [Auth page](https://dashboard.ngrok.com/get-started/your-authtoken)
3. Copy your auth token

#### 3.3 Authenticate ngrok

Run the following command, replacing `YOUR_AUTH_TOKEN` with the token you copied:

```bash
# Windows (from the directory where ngrok.exe is located)
ngrok authtoken YOUR_AUTH_TOKEN

# macOS/Linux
./ngrok authtoken YOUR_AUTH_TOKEN
# Or if installed with Homebrew:
ngrok authtoken YOUR_AUTH_TOKEN
```

This authenticates your ngrok installation with your account, allowing you to create secure tunnels.

</details>

<details>
<summary><h3>Step 4: Configure Environment Variables</h3></summary>

#### 4.1 Create .env File

Create a copy of the example environment file:

```bash
cp .env.example .env
```

#### 4.2 Edit the .env File

Open the `.env` file in your favorite text editor and update the following values:

```ini
# Deepgram API Key
# Get this from https://console.deepgram.com/
DEEPGRAM_API_KEY=your_deepgram_api_key_here

# Twilio Credentials
# Get these from https://console.twilio.com/
TWILIO_ACCOUNT_SID=your_account_sid_here
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE_NUMBER=your_twilio_phone_number  # Format: +1XXXXXXXXXX

# TwiML URL for outbound calls
# You'll get this after creating a TwiML Bin in Step 5
TWILIO_TWIML_URL=https://handler.twilio.com/twiml/your_twiml_bin_id

# Server Configuration
HOST=0.0.0.0  # Listen on all interfaces
PORT=5002     # Port for the WebSocket server
USE_SSL=false # Set to true if using SSL certificates

# Voice Agent Configuration
DEEPGRAM_VOICE=aura-asteria-en       # Voice model to use
DEEPGRAM_LISTEN_MODEL=nova-2         # Speech recognition model
DEEPGRAM_THINK_MODEL=gpt-4o-mini     # AI thinking model
DEEPGRAM_THINK_PROVIDER=open_ai      # AI provider

# Calendar Integration
USE_MOCK_CALENDAR=true               # Set to false to use real Google Calendar
CUSTOMER_NAME=John Doe               # Default customer name
CUSTOMER_EMAIL=john.doe@example.com  # Default customer email
CUSTOMER_PHONE=123-456-7890          # Default customer phone
```

> 💡 **Tip**: For production use, consider using a secure method to manage your environment variables, such as a secrets manager.

</details>

<details>
<summary><h3>Step 5: Set Up Twilio</h3></summary>

#### 5.1 Create a Twilio Account

1. Go to [twilio.com/try-twilio](https://www.twilio.com/try-twilio)
2. Sign up for a new account or log in to an existing one
3. Complete the verification process

#### 5.2 Purchase a Twilio Phone Number

<div align="center">
  <img src="https://i.imgur.com/Yx3oEYv.png" alt="Twilio Phone Number Purchase" width="80%">
</div>

1. Navigate to [Phone Numbers > Buy a Number](https://www.twilio.com/console/phone-numbers/search)
2. Search for a number with **Voice** capabilities
3. Click **Buy** to purchase the number
4. Note down this phone number for your `.env` file

#### 5.3 Get Your Twilio Credentials

<div align="center">
  <img src="https://i.imgur.com/JxFWX9B.png" alt="Twilio Credentials" width="80%">
</div>

1. Go to your [Twilio Console Dashboard](https://www.twilio.com/console)
2. Find your **Account SID** and **Auth Token**
3. Copy these values to your `.env` file:
   ```
   TWILIO_ACCOUNT_SID=AC1234567890abcdef1234567890abcdef
   TWILIO_AUTH_TOKEN=1234567890abcdef1234567890abcdef
   TWILIO_PHONE_NUMBER=+1XXXXXXXXXX  # The number you purchased
   ```

#### 5.4 Create a TwiML Bin

<div align="center">
  <img src="https://i.imgur.com/8QnGUHJ.png" alt="TwiML Bin Creation" width="80%">
</div>

1. Navigate to [Runtime > TwiML Bins](https://www.twilio.com/console/runtime/twiml-bins) in your Twilio Console
2. Click **Create new TwiML Bin**
3. Fill in the following details:
   - **Friendly Name**: `Voice Agent Connection`
   - **TwiML**:
     ```xml
     <?xml version="1.0" encoding="UTF-8"?>
     <Response>
         <Say language="en">This call may be monitored or recorded.</Say>
         <Connect>
             <Stream url="wss://your-ngrok-url.ngrok.io/twilio" />
         </Connect>
     </Response>
     ```
   > ⚠️ **Note**: You'll update the `url` value later after starting ngrok.
4. Click **Create**
5. Copy the TwiML Bin URL (it will look like `https://handler.twilio.com/twiml/EHxxxxx`)
6. Add this URL to your `.env` file as `TWILIO_TWIML_URL`

</details>

<details>
<summary><h3>Step 6: Set Up Google Calendar (Optional)</h3></summary>

> 📝 **Note**: If you set `USE_MOCK_CALENDAR=true` in your `.env` file, you can skip this step.

#### 6.1 Create a Google Cloud Project

<div align="center">
  <img src="https://i.imgur.com/aTtYIgL.png" alt="Google Cloud Project Creation" width="80%">
</div>

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Click the project dropdown at the top of the page
3. Click **NEW PROJECT**
4. Enter a project name (e.g., `Voice Agent Calendar`)
5. Click **CREATE**
6. Wait for the project to be created and select it

#### 6.2 Enable the Google Calendar API

<div align="center">
  <img src="https://i.imgur.com/JQgcWKE.png" alt="Enable Google Calendar API" width="80%">
</div>

1. In your Google Cloud project, go to **APIs & Services > Library**
2. Search for "Google Calendar API"
3. Click on the Google Calendar API card
4. Click **ENABLE**

#### 6.3 Create OAuth Credentials

<div align="center">
  <img src="https://i.imgur.com/Ql2TaV4.png" alt="Create OAuth Credentials" width="80%">
</div>

1. Go to **APIs & Services > Credentials**
2. Click **CREATE CREDENTIALS** and select **OAuth client ID**
3. If prompted to configure the OAuth consent screen:
   - Click **CONFIGURE CONSENT SCREEN**
   - Select **External** user type
   - Fill in the required fields (App name, User support email, Developer contact information)
   - Click **SAVE AND CONTINUE** through the remaining steps
   - Click **BACK TO DASHBOARD** when finished
4. Return to **CREATE CREDENTIALS** > **OAuth client ID**
5. Select **Desktop app** as the application type
6. Enter a name (e.g., `Voice Agent Desktop Client`)
7. Click **CREATE**
8. Click **DOWNLOAD JSON** to download your credentials
9. Rename the downloaded file to `credentials.json`
10. Move the file to the root directory of your project

</details>

<details>
<summary><h3>Step 7: Start the Server</h3></summary>

#### 7.1 Start the Twilio WebSocket Server

<table>
  <tr>
    <th>Windows</th>
    <th>macOS/Linux</th>
  </tr>
  <tr>
    <td>
      
```bash
# Using the batch script
start_twilio_server.bat

# Or directly with Python
python twilio_server.py
```

</td>
    <td>
      
```bash
# Using the shell script
chmod +x start_twilio_server.sh
./start_twilio_server.sh

# Or directly with Python
python twilio_server.py
```

</td>
  </tr>
</table>

You should see output similar to this:

```
============================================================
🚀 Twilio Voice Agent Calendar Scheduler Starting!
============================================================

1. Make sure your TwiML Bin is configured with:
   <Connect><Stream url="wss://your-server-url.com/twilio" /></Connect>

2. Use twilio_client.py to make outbound calls

Press Ctrl+C to stop the server

============================================================
```

#### 7.2 Start ngrok to Expose Your Server

Open a new terminal window (keep the server running in the first one) and run:

```bash
# Replace 5002 with the PORT value from your .env file if different
ngrok http 5002
```

You'll see output like this:

<div align="center">
  <img src="https://i.imgur.com/aSFZNeE.png" alt="ngrok output" width="80%">
</div>

#### 7.3 Update Your TwiML Bin with the ngrok URL

1. Copy the HTTPS URL from ngrok (e.g., `https://a1b2c3d4.ngrok.io`)
2. Go back to your [TwiML Bin](https://www.twilio.com/console/runtime/twiml-bins) in the Twilio Console
3. Edit your TwiML Bin
4. Update the Stream URL to `wss://a1b2c3d4.ngrok.io/twilio` (replace with your actual ngrok URL)
5. Save the updated TwiML Bin

> ⚠️ **Important**: The free version of ngrok generates a new URL each time you restart it. You'll need to update your TwiML Bin with the new URL each time.

</details>

<details>
<summary><h3>Step 8: Make an Outbound Call</h3></summary>

Now you're ready to make your first AI-powered outbound call!

#### 8.1 Run the Twilio Client

```bash
# Format: python twilio_client.py [phone_number]
# Example:
python twilio_client.py +1234567890
```

Replace `+1234567890` with the phone number you want to call (in E.164 format with the country code).

#### 8.2 Monitor the Call

1. Watch the server terminal for logs showing the conversation flow
2. The call recipient will hear the AI agent introduce itself and begin the conversation
3. The agent will attempt to schedule a property viewing appointment

#### 8.3 Call Flow Visualization

<div align="center">
  <img src="https://i.imgur.com/JQgcWKE.png" alt="Call Flow" width="80%">
</div>

1. Your script initiates the call through Twilio
2. Twilio connects to the recipient's phone
3. When answered, Twilio streams audio to your server via WebSockets
4. Your server forwards the audio to Deepgram's Voice Agent
5. Deepgram processes the audio and generates responses
6. Your server forwards the responses back to the call
7. The AI agent handles the conversation flow, including calendar functions

</details>

---

## 🔍 System Architecture

<div align="center">
  <img src="https://mermaid.ink/img/pako:eNqNVE1v2zAM_SuETgOaJE3TJMiwHXbYKWiwYcCOQ1HQEu0IlSVDkpMGRf77KH_ESRdsBxu2-Ph4JB-pO1RYEYzRVJZCVjB7lUJXoB3MhC61MDAHVUBlQFrlQFmtHLyBAWdzCcZqcJWBqTYarIXSwFoZBx_CQCVh4WAlbAGVVQ5qKISy8A5GGJgL5aCEjbIOVK1KAytlHHyAgUIUUEFl2xK0UQ4-oRTawRcYyIV2UAjt4FZoB99gIBPawUZoBzdCO_gBA5nQDtZCO1gI7eBXGEi1hV8w8CaUg3ehHPyBgTehHHwI5eAJDLwI5eBZKAePYOBJKAcPQjm4BwMzoRzcCeXgFgxcC-XgSigHl2DgXCgHZ0I5OAMDp0I5OBHKwTEYOBTKwaFQDg7AwL5QDvaFcrAHBnaFcrAjlINtMLAllINNoRxsgIF1oRysC-VgFQysCOVgWSgHS2BgUSgHC0I5mAcDc0I5mBXKwTgYmBHKwbRQDkbBwJRQDsaFcjACBoaFcjAklIMBMDAglIN-oRz0gYFeoRz0COWgGwx0CeWgUygH7WCgTSgHrUI5aAUDzUI5aBLKQSMYaBDKQb1QDurAQK1QDmqEclANBqqEclAplIMKMFAulIMyoRyUgoESoRwUC-WgCAwUCuUgEMpBPhj4B1Hl-Qs?type=png" alt="System Architecture" width="100%">
</div>

### Component Interaction

1. **Twilio Client (`twilio_client.py`)**
   - Initiates outbound calls using Twilio's REST API
   - Configures calls to connect to your WebSocket server

2. **TwiML Bin**
   - Provides instructions to Twilio on how to handle the call
   - Establishes WebSocket connection to your server

3. **WebSocket Server (`twilio_server.py`)**
   - Handles WebSocket connections from Twilio
   - Manages audio streaming between Twilio and Deepgram
   - Processes function calls for calendar operations

4. **Deepgram Voice Agent**
   - Converts speech to text (STT)
   - Processes conversation with AI models
   - Generates natural language responses
   - Converts text to speech (TTS)

5. **Calendar Integration**
   - Authenticates with Google Calendar API
   - Checks availability for appointments
   - Creates calendar events for scheduled appointments

---

## 🛠️ Advanced Configuration

<details>
<summary><h3>Voice and Model Configuration</h3></summary>

You can customize the AI voice and models by modifying these variables in your `.env` file:

```ini
# Voice Agent Configuration
DEEPGRAM_VOICE=aura-asteria-en       # Voice model to use
DEEPGRAM_LISTEN_MODEL=nova-2         # Speech recognition model
DEEPGRAM_THINK_MODEL=gpt-4o-mini     # AI thinking model
DEEPGRAM_THINK_PROVIDER=open_ai      # AI provider
```

Available options:

**Voices:**
- `aura-asteria-en` - Female voice (default)
- `aura-athena-en` - Female voice (alternative)
- `aura-orion-en` - Male voice
- `aura-perseus-en` - Male voice (alternative)

**Listen Models:**
- `nova-2` - High accuracy speech recognition (default)
- `nova-1` - Older model, may be faster

**Think Models:**
- `gpt-4o-mini` - Balanced performance and cost (default)
- `gpt-4o` - Higher quality but more expensive
- `claude-3-opus` - Alternative model (requires DEEPGRAM_THINK_PROVIDER=anthropic)

</details>

<details>
<summary><h3>SSL Configuration</h3></summary>

For production deployments, you should use SSL:

1. Set `USE_SSL=true` in your `.env` file
2. Provide paths to your SSL certificate and key:
   ```ini
   SSL_CERT=path/to/cert.pem
   SSL_KEY=path/to/key.pem
   ```
3. Update your TwiML Bin URL to use `wss://` instead of `ws://`

To generate a self-signed certificate for testing:

```bash
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
```

</details>

<details>
<summary><h3>Customizing the AI Prompt</h3></summary>

You can customize the AI's behavior by modifying the `PROMPT_TEMPLATE` in `twilio_server.py`. This template provides instructions to the AI about how to respond to callers.

Key sections you might want to customize:

1. **Personality & Tone**: Adjust how formal or casual the agent sounds
2. **Outbound Call Flow**: Change the conversation structure
3. **Information to Collect**: Modify what data the agent gathers
4. **Handling Common Responses**: Add more scenarios the agent should handle

Example modification to make the agent more casual:

```python
PROMPT_TEMPLATE = """You are a friendly and casual real estate appointment scheduler for Premium Properties. Your role is to proactively call potential buyers to schedule property viewings in Google Calendar.

PERSONALITY & TONE:
- Be warm, friendly, and conversational
- Use casual language and contractions (I'm, you're, let's)
- Show enthusiasm with occasional exclamations
- Sound like you're genuinely excited about the properties
- Use conversational fillers like "you know" and "actually" occasionally

# ... rest of the prompt
"""
```

</details>

---

## 🔧 Troubleshooting

<details>
<summary><h3>Connection Issues</h3></summary>

#### Twilio Can't Connect to Your Server

**Symptoms:**
- Call connects but no AI voice is heard
- Server logs show no incoming WebSocket connections
- Error in Twilio logs: "Failed to connect to WebSocket"

**Solutions:**
1. **Check ngrok Status**
   - Ensure ngrok is running and the tunnel is active
   - Verify the ngrok URL in your TwiML Bin matches the current ngrok URL
   - Try restarting ngrok and updating the TwiML Bin

2. **Verify Server Configuration**
   - Confirm the server is running on the port specified in your `.env` file
   - Check that the server is listening on all interfaces (`HOST=0.0.0.0`)
   - Try a different port if the current one might be blocked

3. **Network Issues**
   - Check if your firewall is blocking WebSocket connections
   - Ensure your internet connection is stable
   - Try using a different network if possible

#### Server Can't Connect to Deepgram

**Symptoms:**
- Server logs show "Failed to connect to Deepgram"
- No response from the AI agent during calls

**Solutions:**
1. **API Key Issues**
   - Verify your Deepgram API key is correct
   - Check that your Deepgram account is active and has sufficient credits
   - Ensure your API key has Voice Agent capabilities enabled

2. **Network Connectivity**
   - Check your internet connection
   - Verify that outbound connections to Deepgram's servers are allowed
   - Try using a different network if possible

</details>

<details>
<summary><h3>Audio Issues</h3></summary>

#### No Audio from the AI Agent

**Symptoms:**
- Call connects but the AI agent can't be heard
- Server logs show successful connections but no audio output

**Solutions:**
1. **Audio Format Configuration**
   - Verify the audio settings in the server configuration match Twilio's requirements
   - Check that the `mulaw` encoding and `8000` Hz sample rate are correctly set

2. **Deepgram Voice Configuration**
   - Ensure the selected voice model is available in your Deepgram account
   - Try a different voice model by changing `DEEPGRAM_VOICE` in your `.env` file

3. **Debugging Audio Flow**
   - Add additional logging to track audio packets through the system
   - Check if audio data is being received from Deepgram but not forwarded to Twilio

#### Poor Audio Quality

**Symptoms:**
- AI voice is choppy or robotic
- Words are cut off or unintelligible

**Solutions:**
1. **Network Bandwidth**
   - Ensure your server has sufficient bandwidth for real-time audio streaming
   - Try reducing other network activity during calls

2. **Buffer Size Adjustment**
   - Modify the `BUFFER_SIZE` in `twilio_server.py` to optimize for your network conditions
   - Increase for stability, decrease for lower latency

</details>

<details>
<summary><h3>Calendar Issues</h3></summary>

#### Authentication Failures

**Symptoms:**
- Server logs show "Failed to authenticate with Google Calendar"
- AI agent can't check availability or schedule appointments

**Solutions:**
1. **Credentials File**
   - Ensure `credentials.json` is correctly formatted and in the project root directory
   - Verify the file contains valid OAuth client credentials

2. **OAuth Flow**
   - Run the server once with a browser available to complete the OAuth flow
   - Check for browser windows that might open during the authentication process
   - Follow the prompts to grant calendar access

3. **Token Expiration**
   - Delete `token.pickle` if it exists and restart the server to force re-authentication
   - Ensure your Google Cloud project has not expired or been disabled

#### Calendar API Errors

**Symptoms:**
- Server logs show "Error getting available slots" or "Error scheduling appointment"
- AI agent reports calendar errors during calls

**Solutions:**
1. **API Enablement**
   - Verify the Google Calendar API is enabled in your Google Cloud project
   - Check API quotas and limits in the Google Cloud Console

2. **Permissions**
   - Ensure the authenticated user has permission to access and modify the calendar
   - Check that the correct calendar ID is being used (default is 'primary')

3. **Date Format Issues**
   - Verify that dates are being properly formatted in RFC3339 format
   - Check for timezone inconsistencies in date handling

</details>

---

## 📊 Performance Monitoring

<details>
<summary><h3>Logging and Debugging</h3></summary>

The application uses Python's built-in logging module to provide detailed information about its operation. Logs are output to the console by default.

#### Log Levels

- **INFO**: Normal operation messages
- **ERROR**: Problems that need attention
- **DEBUG**: Detailed information for troubleshooting (disabled by default)

#### Enabling Debug Logging

To enable more detailed logging, modify the logging configuration in `twilio_server.py`:

```python
logging.basicConfig(
    level=logging.DEBUG,  # Change from INFO to DEBUG
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

#### Key Log Messages to Watch For

- `"Twilio handler started"`: Indicates a new call connection
- `"Function call received: [function_name]"`: Shows when the AI agent is performing a calendar operation
- `"Error in [component]: [error_message]"`: Indicates a problem that needs attention

</details>

<details>
<summary><h3>Call Analytics</h3></summary>

To track call performance and outcomes, you can use Twilio's built-in analytics:

1. Go to the [Twilio Console](https://www.twilio.com/console)
2. Navigate to **Monitor > Logs > Calls**
3. View detailed information about each call, including:
   - Duration
   - Status (completed, failed, etc.)
   - Cost
   - Call quality metrics

For more advanced analytics, consider implementing custom tracking by:

1. Adding a database to store call outcomes
2. Logging key conversation events (appointment scheduled, call ended, etc.)
3. Creating a dashboard to visualize performance metrics

</details>

---

## 📚 Additional Resources

<div align="center">
  <table>
    <tr>
      <td align="center" width="33%">
        <img src="https://i.imgur.com/4LL82wp.png" width="100" height="100"><br>
        <h3>API Documentation</h3>
        <a href="https://www.twilio.com/docs/voice">Twilio Voice API</a><br>
        <a href="https://developers.deepgram.com/docs/voice-agent-api">Deepgram Voice Agent API</a><br>
        <a href="https://developers.google.com/calendar">Google Calendar API</a>
      </td>
      <td align="center" width="33%">
        <img src="https://i.imgur.com/Ql2TaV4.png" width="100" height="100"><br>
        <h3>Tools & Utilities</h3>
        <a href="https://ngrok.com/docs">ngrok Documentation</a><br>
        <a href="https://www.twilio.com/docs/runtime/tutorials/twiml-bins">TwiML Bins Guide</a><br>
        <a href="https://developers.deepgram.com/docs/voice-agent-prompt-engineering">Prompt Engineering Guide</a>
      </td>
      <td align="center" width="33%">
        <img src="https://i.imgur.com/Cda9UR4.png" width="100" height="100"><br>
        <h3>Learning Resources</h3>
        <a href="https://www.twilio.com/blog/category/tutorials">Twilio Tutorials</a><br>
        <a href="https://developers.deepgram.com/learn/">Deepgram Learn</a><br>
        <a href="https://developers.google.com/calendar/api/guides/overview">Calendar API Guides</a>
      </td>
    </tr>
  </table>
</div>

---

## 📄 License

<div align="center">
  
MIT License

Copyright (c) 2023 Amruth

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

</div>

---

<div align="center">
  <p>
    <a href="https://github.com/Amruth22/voice-agent/issues">Report Bug</a>
    ·
    <a href="https://github.com/Amruth22/voice-agent/issues">Request Feature</a>
  </p>
  <p>Made with ❤️ by <a href="https://github.com/Amruth22">Amruth</a></p>
</div>