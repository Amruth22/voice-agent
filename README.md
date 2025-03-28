# Voice Agent with Google Calendar Integration

This repository contains a voice agent application that collects customer details and schedules meetings in Google Calendar. It's inspired by the [flask-agent-function-calling-demo](https://github.com/deepgram-devs/flask-agent-function-calling-demo) by Deepgram.

## Features

- Web interface for customer interaction
- Voice recognition for hands-free operation
- Text input option for typing instead of speaking
- Google Calendar integration for appointment scheduling
- Available time slot checking
- Appointment confirmation and email notifications
- Real-time conversation display
- Audio playback of agent responses

## Screenshots

![Voice Agent Web Interface](https://via.placeholder.com/800x450.png?text=Voice+Agent+Web+Interface)

## Requirements

- Python 3.7+
- Google Cloud Platform account with Calendar API enabled
- OAuth 2.0 credentials for Google Calendar API
- Deepgram API key for voice agent functionality

## Setup

1. Clone this repository:
   ```
   git clone https://github.com/Amruth22/voice-agent.git
   cd voice-agent
   ```

2. Install required packages:
   ```
   pip install -r requirements.txt
   ```

3. Set up Google Calendar API:
   - Go to the [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project
   - Enable the Google Calendar API
   - Create OAuth 2.0 credentials (Desktop application)
   - Download the credentials JSON file and save it as `credentials.json` in the project directory

4. Set up Deepgram API:
   - Sign up for a [Deepgram account](https://console.deepgram.com/signup)
   - Create a new API key with Nova ASR and Voice Agent capabilities
   - Set the API key as an environment variable:
     ```
     export DEEPGRAM_API_KEY=your_api_key_here
     ```

## Usage

### Web Interface

Run the Flask application to start the web interface:

```
python app.py
```

Then open your browser to http://127.0.0.1:5000 to access the web interface.

1. Select your microphone and speaker devices from the dropdown menus
2. Click "Start Voice Agent" to begin
3. Speak to the agent or type in the text box
4. The agent will guide you through scheduling an appointment
5. Once complete, you'll see the appointment details and receive an email confirmation

### Console Interface

Alternatively, you can use the console interface:

```
python google_calendar_scheduler.py
```

The script will:
1. Prompt you to enter customer details (name, email, phone)
2. Ask you to select an appointment type
3. Show available time slots from Google Calendar
4. Schedule the appointment and send an email invitation to the customer

## Authentication

On first run, the application will open a browser window asking you to authorize it to access your Google Calendar. After authorization, a token will be saved locally for future use.

## Project Structure

- `app.py` - Flask web application with SocketIO for real-time communication
- `google_calendar_scheduler.py` - Console-based appointment scheduler
- `templates/` - HTML templates for the web interface
- `static/` - CSS, JavaScript, and other static assets
- `credentials.json` - Google OAuth credentials (you need to provide this)
- `token.pickle` - Saved authentication token (generated on first run)

## Future Enhancements

- SMS notifications for appointment reminders
- Integration with CRM systems
- Multi-language support
- Calendar sharing options
- Recurring appointment scheduling

## License

MIT