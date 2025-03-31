import requests
import os

def download_file(url, local_filename):
    """Download a file from a URL to a local file"""
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192): 
                f.write(chunk)
    return local_filename

# URL of the fixed twilio_server.py file
file_url = "https://raw.githubusercontent.com/Amruth22/voice-agent/twilio-with-functions/twilio_server.py"

# Download the file
print("Downloading fixed twilio_server.py file...")
download_file(file_url, "twilio_server.py")
print("Download complete! You can now run the server with: python twilio_server.py")