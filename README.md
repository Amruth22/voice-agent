# Voice Agent with Google Calendar Integration (Heroku Deployment)

This repository contains a voice agent application that collects customer details and schedules meetings in Google Calendar. This branch is specifically configured for deployment on Heroku.

## Features

- Web interface for customer interaction
- Voice recognition for hands-free operation
- Text input option for typing instead of speaking
- Google Calendar integration for appointment scheduling
- Available time slot checking
- Appointment confirmation and email notifications
- Real-time conversation display
- Audio playback of agent responses

## Heroku Deployment Instructions

### Prerequisites

1. A [Heroku](https://heroku.com) account
2. The [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli) installed
3. A Deepgram API key with Voice Agent capabilities
4. Google Calendar API credentials (optional, can use mock calendar)

### Deployment Steps

1. Clone this repository and navigate to the heroku-deployment branch:
   ```
   git clone https://github.com/Amruth22/voice-agent.git
   cd voice-agent
   git checkout heroku-deployment
   ```

2. Log in to Heroku and create a new app:
   ```
   heroku login
   heroku create your-voice-agent-app
   ```

3. Add the Heroku apt buildpack for PyAudio dependencies:
   ```
   heroku buildpacks:add --index 1 heroku-community/apt
   heroku buildpacks:add --index 2 heroku/python
   ```

4. Set the required environment variables:
   ```
   heroku config:set DEEPGRAM_API_KEY=your_deepgram_api_key
   heroku config:set USE_MOCK_CALENDAR=true
   ```

5. (Optional) If you want to use real Google Calendar integration, you have two options:

   **Option 1: Upload credentials.json to Heroku** (not recommended for security reasons)
   - Include credentials.json in your repository
   - Set `USE_MOCK_CALENDAR=false`

   **Option 2: Use environment variables for credentials** (recommended)
   ```
   heroku config:set USE_ENV_CREDENTIALS=true
   heroku config:set GOOGLE_CREDENTIALS='{"token": "your_token", "refresh_token": "your_refresh_token", "token_uri": "https://oauth2.googleapis.com/token", "client_id": "your_client_id", "client_secret": "your_client_secret", "scopes": ["https://www.googleapis.com/auth/calendar"]}'
   ```

6. Deploy to Heroku:
   ```
   git push heroku heroku-deployment:main
   ```

7. Open your application:
   ```
   heroku open
   ```

### Additional Configuration

1. **Scaling Dynos**: For better performance, you may want to use a larger dyno:
   ```
   heroku ps:scale web=1:standard-1x
   ```

2. **Prevent Dyno Sleep**: To prevent your app from sleeping (free tier only):
   ```
   heroku ps:scale web=1:hobby
   ```

3. **Logs**: To view logs in real-time:
   ```
   heroku logs --tail
   ```

4. **Custom Domain**: To add a custom domain:
   ```
   heroku domains:add www.yourdomain.com
   ```

## Local Development

To run the application locally:

1. Install required packages:
   ```
   pip install -r requirements.txt
   ```

2. Set up environment variables:
   ```
   export DEEPGRAM_API_KEY=your_api_key_here
   export USE_MOCK_CALENDAR=true
   ```

3. Run the Flask application:
   ```
   python app.py
   ```

4. Open your browser to http://127.0.0.1:5000

## Troubleshooting

1. **PyAudio Issues**: If you encounter issues with PyAudio on Heroku, check the buildpack logs:
   ```
   heroku logs --source app --dyno build
   ```

2. **WebSocket Connection Issues**: If WebSocket connections are failing, ensure you're using the correct protocol (wss:// for HTTPS, ws:// for HTTP).

3. **Google Calendar Authentication**: If you're having issues with Google Calendar authentication, try using the mock calendar option first to ensure the rest of the application is working.

## Project Structure

- `app.py` - Flask web application with SocketIO for real-time communication
- `Procfile` - Heroku process file that specifies how to run the application
- `runtime.txt` - Specifies the Python version for Heroku
- `apt-packages` - Lists system dependencies required by PyAudio
- `requirements.txt` - Python dependencies
- `templates/` - HTML templates for the web interface
- `static/` - CSS, JavaScript, and other static assets

## License

MIT