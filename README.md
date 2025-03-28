# Voice Agent with Google Calendar Integration

This repository contains a voice agent application that collects customer details and schedules meetings in Google Calendar. It's inspired by the [flask-agent-function-calling-demo](https://github.com/deepgram-devs/flask-agent-function-calling-demo) by Deepgram.

## Features

- Customer data collection through console interface
- Google Calendar integration for appointment scheduling
- Available time slot checking
- Appointment confirmation and email notifications

## Requirements

- Python 3.7+
- Google Cloud Platform account with Calendar API enabled
- OAuth 2.0 credentials for Google Calendar API

## Setup

1. Clone this repository:
   ```
   git clone https://github.com/Amruth22/voice-agent.git
   cd voice-agent
   ```

2. Install required packages:
   ```
   pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
   ```

3. Set up Google Calendar API:
   - Go to the [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project
   - Enable the Google Calendar API
   - Create OAuth 2.0 credentials (Desktop application)
   - Download the credentials JSON file and save it as `credentials.json` in the project directory

## Usage

Run the script to start the appointment scheduler:

```
python google_calendar_scheduler.py
```

The script will:
1. Prompt you to enter customer details (name, email, phone)
2. Ask you to select an appointment type
3. Show available time slots from Google Calendar
4. Schedule the appointment and send an email invitation to the customer

## Authentication

On first run, the script will open a browser window asking you to authorize the application to access your Google Calendar. After authorization, a token will be saved locally for future use.

## Future Enhancements

- Web interface for customer data collection
- Voice recognition for hands-free operation
- SMS notifications for appointment reminders
- Integration with CRM systems

## License

MIT