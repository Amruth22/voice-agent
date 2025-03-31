# Voice Agent with Google Calendar Integration (Vercel Deployment)

This repository contains a voice agent application that collects customer details and schedules meetings in Google Calendar. This branch is specifically configured for deployment on Vercel.

## Features

- Web interface for customer interaction
- Text input for typing instead of speaking
- Mock calendar integration for demonstration purposes
- Real-time conversation display
- Appointment confirmation

## Vercel Deployment Instructions

### Prerequisites

1. A [Vercel](https://vercel.com) account
2. The [Vercel CLI](https://vercel.com/docs/cli) installed (optional, for local testing)

### Deployment Steps

1. Fork or clone this repository
   ```
   git clone https://github.com/Amruth22/voice-agent.git
   cd voice-agent
   git checkout vercel-deployment
   ```

2. Deploy to Vercel using one of these methods:

   **Option 1: Vercel Dashboard**
   - Go to [Vercel Dashboard](https://vercel.com/dashboard)
   - Click "New Project"
   - Import your GitHub repository
   - Select the "vercel-deployment" branch
   - Click "Deploy"

   **Option 2: Vercel CLI**
   ```
   vercel login
   vercel
   ```

3. Set environment variables in the Vercel dashboard:
   - `DEEPGRAM_API_KEY`: Your Deepgram API key (for full functionality)
   - `USE_MOCK_CALENDAR`: Set to "true" for demo purposes

### Important Notes for Vercel Deployment

1. **Limited Functionality**: The Vercel deployment has limited functionality compared to the full application:
   - No microphone access (text input only)
   - Uses mock calendar data instead of real Google Calendar integration
   - No real-time voice interaction

2. **WebSocket Support**: Vercel has limited WebSocket support. The application uses a simplified communication model for the Vercel deployment.

3. **Environment Variables**: Make sure to set the required environment variables in the Vercel dashboard.

## Local Development

To run the application locally:

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Run the Flask application:
   ```
   python app.py
   ```

3. Open your browser to http://127.0.0.1:5000

## Project Structure

- `app.py` - Flask web application with SocketIO for real-time communication
- `vercel.json` - Vercel configuration file
- `templates/` - HTML templates for the web interface
- `static/` - CSS, JavaScript, and other static assets

## License

MIT