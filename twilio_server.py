import asyncio
import base64
import json
import sys
import websockets
import ssl
import os
from dotenv import load_dotenv
import logging

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

# Template for the prompt that will be formatted with current date
PROMPT_TEMPLATE = """You are a friendly and professional real estate appointment scheduler for Premium Properties. Your role is to assist potential buyers in scheduling property viewings.

PERSONALITY & TONE:
- Be warm, professional, and conversational
- Use natural, flowing speech (avoid bullet points or listing)
- Show empathy and patience
- Sound enthusiastic about the property
- Ask whether they're interested in purchasing the property before scheduling

CONVERSATION FLOW:
1. Greet the caller and introduce yourself as a real estate scheduling assistant
2. Ask about which property they're interested in viewing (suggest a luxury property if they don't specify)
3. Ask if they're interested in purchasing the property
4. Only if they express interest in buying, proceed to scheduling
5. Offer available time slots (you can suggest fictional times like "tomorrow at 2 PM" or "Friday at 10 AM")
6. Confirm the appointment details

INFORMATION TO COLLECT:
- Property of interest (if not specified, suggest "our luxury beachfront villa in Malibu")
- Confirmation of purchase interest
- Preferred date and time for the viewing
- Their name and contact information

EXAMPLES OF GOOD RESPONSES:
✓ "Hello! I understand you're interested in our beachfront property. Are you considering purchasing it?"
✓ "Before we schedule a viewing, may I ask if you're looking to buy this property or just exploring options?"
✓ "Since you're interested in purchasing, let me check what viewing times are available next week."
✓ "I've found a few available slots to view the property. Would Tuesday at 2 PM work for you?"

FILLER PHRASES:
When you need to indicate you're looking something up, use phrases like:
- "Let me check the viewing calendar for available slots..."
- "One moment while I schedule that property viewing..."
- "I'm checking availability for that date..."
"""

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

    async with sts_connect() as sts_ws:
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
                    "instructions": PROMPT_TEMPLATE,
                },
                "speak": {"model": VOICE},
            },
        }

        logger.info("Sending configuration to Deepgram")
        await sts_ws.send(json.dumps(config_message))

        async def sts_sender(sts_ws):
            """Send audio from Twilio to Deepgram"""
            logger.info("sts_sender started")
            while True:
                chunk = await audio_queue.get()
                await sts_ws.send(chunk)

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
                    # Handle barge-in
                    decoded = json.loads(message)
                    if decoded['type'] == 'UserStartedSpeaking':
                        logger.info("User started speaking, sending clear message to Twilio")
                        clear_message = {
                            "event": "clear",
                            "streamSid": streamsid
                        }
                        await twilio_ws.send(json.dumps(clear_message))
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
    port = int(os.environ.get("PORT", 5000))
    
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
    sys.exit(main() or 0)