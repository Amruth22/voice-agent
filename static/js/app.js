// Connect to Socket.IO server
const socket = io();

// DOM elements
const chatContainer = document.getElementById('chatContainer');
const userInput = document.getElementById('userInput');
const sendButton = document.getElementById('sendButton');
const startButton = document.getElementById('startButton');
const stopButton = document.getElementById('stopButton');
const micToggle = document.getElementById('micToggle');
const inputDeviceSelect = document.getElementById('inputDevice');
const outputDeviceSelect = document.getElementById('outputDevice');
const logContainer = document.getElementById('logContainer');
const appointmentDetails = document.getElementById('appointmentDetails');
const agentAudio = document.getElementById('agentAudio');

// State variables
let isAgentRunning = false;
let isAgentSpeaking = false;
let typingIndicator = null;
let audioErrorsReported = false;
let audioEnabled = true;

// Initialize the page
document.addEventListener('DOMContentLoaded', () => {
    // Load audio devices
    loadAudioDevices();
    
    // Set up event listeners
    setupEventListeners();
    
    // Check if we're running on Heroku
    checkEnvironment();
});

// Check if we're running on Heroku or another environment
function checkEnvironment() {
    // Check if we're running on Heroku by looking at the hostname
    const isHeroku = window.location.hostname.includes('herokuapp.com');
    
    if (isHeroku) {
        addLogEntry('Running on Heroku - audio playback may be limited', 'warning');
        // Add a notice at the top of the chat
        const noticeElement = document.createElement('div');
        noticeElement.className = 'alert alert-info mb-3';
        noticeElement.innerHTML = `
            <strong>Note:</strong> This application is running on Heroku with limited audio capabilities. 
            Text-based interaction is fully supported, but voice interaction may not work properly.
        `;
        chatContainer.prepend(noticeElement);
    }
}

// Load available audio devices
function loadAudioDevices() {
    fetch('/api/devices')
        .then(response => response.json())
        .then(data => {
            // Clear existing options
            inputDeviceSelect.innerHTML = '';
            outputDeviceSelect.innerHTML = '';
            
            // Add input devices
            data.input.forEach(device => {
                const option = document.createElement('option');
                option.value = device.deviceId;
                option.textContent = device.name;
                inputDeviceSelect.appendChild(option);
            });
            
            // Add output devices
            data.output.forEach(device => {
                const option = document.createElement('option');
                option.value = device.deviceId;
                option.textContent = device.name;
                outputDeviceSelect.appendChild(option);
            });
            
            // Check if these are mock devices
            if (data.mock) {
                addLogEntry('Using mock audio devices - audio functionality will be limited', 'warning');
                micToggle.disabled = true;
                micToggle.checked = false;
                
                // Add a note to the device selects
                const mockNote = document.createElement('small');
                mockNote.className = 'text-muted d-block mt-2';
                mockNote.textContent = 'Audio devices not available in this environment';
                inputDeviceSelect.parentNode.appendChild(mockNote.cloneNode(true));
                outputDeviceSelect.parentNode.appendChild(mockNote);
            } else {
                addLogEntry('Audio devices loaded successfully');
            }
        })
        .catch(error => {
            addLogEntry(`Error loading audio devices: ${error.message}`, 'error');
        });
}

// Set up event listeners
function setupEventListeners() {
    // Start button
    startButton.addEventListener('click', () => {
        if (!isAgentRunning) {
            startVoiceAgent();
        }
    });
    
    // Stop button
    stopButton.addEventListener('click', () => {
        if (isAgentRunning) {
            stopVoiceAgent();
        }
    });
    
    // Send button
    sendButton.addEventListener('click', () => {
        sendUserMessage();
    });
    
    // Enter key in input field
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendUserMessage();
        }
    });
    
    // Microphone toggle
    micToggle.addEventListener('change', () => {
        // This will be handled by the voice agent
        addLogEntry(`Microphone ${micToggle.checked ? 'enabled' : 'disabled'}`);
    });
    
    // Audio error handling
    agentAudio.addEventListener('error', (e) => {
        handleAudioError(e);
    });
    
    // Socket.IO event listeners
    setupSocketListeners();
}

// Handle audio errors gracefully
function handleAudioError(error) {
    // Only report audio errors once to avoid flooding the logs
    if (!audioErrorsReported) {
        audioErrorsReported = true;
        audioEnabled = false;
        
        // Log the error once
        addLogEntry('Audio playback not available in this environment. Using text-only mode.', 'warning');
        
        // Disable the audio toggle
        micToggle.disabled = true;
        micToggle.checked = false;
    }
}

// Set up Socket.IO event listeners
function setupSocketListeners() {
    // Conversation updates
    socket.on('conversation_update', (data) => {
        if (data.role === 'user') {
            addUserMessage(data.content);
        } else if (data.role === 'assistant') {
            addAssistantMessage(data.content);
        }
    });
    
    // Audio chunks
    socket.on('audio_chunk', (data) => {
        if (!isAgentSpeaking) {
            isAgentSpeaking = true;
            updateSpeakingIndicator(true);
        }
        
        // Only try to play audio if it's enabled
        if (audioEnabled) {
            // Play audio
            const audioData = base64ToArrayBuffer(data.audio);
            playAudioChunk(audioData);
        }
    });
    
    // Log messages
    socket.on('log_message', (data) => {
        addLogEntry(data.message);
    });
    
    // Appointment scheduled
    socket.on('appointment_scheduled', (data) => {
        updateAppointmentDetails(data);
    });
    
    // Conversation ended
    socket.on('conversation_ended', (data) => {
        addLogEntry(`Conversation ended: ${data.message}`);
        setTimeout(() => {
            stopVoiceAgent();
        }, 5000);
    });
}

// Start the voice agent
function startVoiceAgent() {
    const inputDeviceId = inputDeviceSelect.value;
    const outputDeviceId = outputDeviceSelect.value;
    
    socket.emit('start_voice_agent', {
        inputDeviceId,
        outputDeviceId
    });
    
    isAgentRunning = true;
    startButton.disabled = true;
    stopButton.disabled = false;
    
    // Only enable microphone toggle if audio is available
    if (!micToggle.disabled) {
        micToggle.checked = true;
    }
    
    addLogEntry('Voice agent started');
}

// Stop the voice agent
function stopVoiceAgent() {
    socket.emit('stop_voice_agent');
    
    isAgentRunning = false;
    isAgentSpeaking = false;
    startButton.disabled = false;
    stopButton.disabled = true;
    
    // Only change microphone toggle if it's not disabled
    if (!micToggle.disabled) {
        micToggle.checked = false;
    }
    
    updateSpeakingIndicator(false);
    
    addLogEntry('Voice agent stopped');
}

// Send a user message
function sendUserMessage() {
    const message = userInput.value.trim();
    if (message && isAgentRunning) {
        // Add message to chat
        addUserMessage(message);
        
        // Send to server
        socket.emit('send_text', { text: message });
        
        // Clear input
        userInput.value = '';
        
        // Show typing indicator
        showTypingIndicator();
    }
}

// Add a user message to the chat
function addUserMessage(message) {
    const messageElement = document.createElement('div');
    messageElement.className = 'message user';
    
    const contentElement = document.createElement('div');
    contentElement.className = 'message-content';
    contentElement.textContent = message;
    
    const timeElement = document.createElement('div');
    timeElement.className = 'message-time';
    timeElement.textContent = getCurrentTime();
    
    messageElement.appendChild(contentElement);
    messageElement.appendChild(timeElement);
    
    // Remove typing indicator if present
    removeTypingIndicator();
    
    chatContainer.appendChild(messageElement);
    scrollToBottom();
}

// Add an assistant message to the chat
function addAssistantMessage(message) {
    // Remove typing indicator if present
    removeTypingIndicator();
    
    const messageElement = document.createElement('div');
    messageElement.className = 'message assistant';
    
    const contentElement = document.createElement('div');
    contentElement.className = 'message-content';
    
    // Add speaking indicator if agent is speaking and audio is enabled
    if (isAgentSpeaking && audioEnabled) {
        const speakingIndicator = document.createElement('span');
        speakingIndicator.className = 'speaking-indicator';
        contentElement.appendChild(speakingIndicator);
    }
    
    contentElement.appendChild(document.createTextNode(message));
    
    const timeElement = document.createElement('div');
    timeElement.className = 'message-time';
    timeElement.textContent = getCurrentTime();
    
    messageElement.appendChild(contentElement);
    messageElement.appendChild(timeElement);
    
    chatContainer.appendChild(messageElement);
    scrollToBottom();
}

// Show typing indicator
function showTypingIndicator() {
    // Remove existing indicator if present
    removeTypingIndicator();
    
    typingIndicator = document.createElement('div');
    typingIndicator.className = 'message assistant';
    
    const indicatorContent = document.createElement('div');
    indicatorContent.className = 'typing-indicator';
    
    for (let i = 0; i < 3; i++) {
        const dot = document.createElement('span');
        indicatorContent.appendChild(dot);
    }
    
    typingIndicator.appendChild(indicatorContent);
    chatContainer.appendChild(typingIndicator);
    scrollToBottom();
}

// Remove typing indicator
function removeTypingIndicator() {
    if (typingIndicator && typingIndicator.parentNode === chatContainer) {
        chatContainer.removeChild(typingIndicator);
        typingIndicator = null;
    }
}

// Update speaking indicator
function updateSpeakingIndicator(isSpeaking) {
    isAgentSpeaking = isSpeaking;
    
    // Only update speaking indicator if audio is enabled
    if (!audioEnabled) return;
    
    // Update the last assistant message if it exists
    const assistantMessages = document.querySelectorAll('.message.assistant');
    if (assistantMessages.length > 0) {
        const lastMessage = assistantMessages[assistantMessages.length - 1];
        const contentElement = lastMessage.querySelector('.message-content');
        
        if (isSpeaking) {
            // Add indicator if not present
            if (!contentElement.querySelector('.speaking-indicator')) {
                const indicator = document.createElement('span');
                indicator.className = 'speaking-indicator';
                contentElement.insertBefore(indicator, contentElement.firstChild);
            }
        } else {
            // Remove indicator if present
            const indicator = contentElement.querySelector('.speaking-indicator');
            if (indicator) {
                contentElement.removeChild(indicator);
            }
        }
    }
}

// Update appointment details
function updateAppointmentDetails(data) {
    const customer = data.customer;
    const appointment = data.appointment;
    
    const appointmentTime = new Date(customer.appointment_time);
    const formattedTime = appointmentTime.toLocaleString('en-US', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: 'numeric',
        minute: 'numeric',
        hour12: true
    });
    
    appointmentDetails.innerHTML = `
        <div class="alert alert-success mb-3">
            <i class="bi bi-check-circle-fill me-2"></i>
            Appointment Scheduled!
        </div>
        <div class="mb-2">
            <span class="detail-label">Name:</span>
            <span class="detail-value">${customer.name}</span>
        </div>
        <div class="mb-2">
            <span class="detail-label">Email:</span>
            <span class="detail-value">${customer.email}</span>
        </div>
        ${customer.phone ? `
        <div class="mb-2">
            <span class="detail-label">Phone:</span>
            <span class="detail-value">${customer.phone}</span>
        </div>
        ` : ''}
        <div class="mb-2">
            <span class="detail-label">Type:</span>
            <span class="detail-value">${customer.appointment_type}</span>
        </div>
        <div class="mb-2">
            <span class="detail-label">Time:</span>
            <span class="detail-value">${formattedTime}</span>
        </div>
        <div class="mt-3">
            <a href="${appointment.event_link}" target="_blank" class="btn btn-sm btn-primary">
                <i class="bi bi-calendar-event me-1"></i>
                View in Calendar
            </a>
        </div>
    `;
    
    addLogEntry(`Appointment scheduled for ${customer.name} on ${formattedTime}`, 'success');
}

// Add a log entry
function addLogEntry(message, type = 'info') {
    const logEntry = document.createElement('div');
    logEntry.className = 'log-entry';
    
    // Add timestamp
    const timestamp = getCurrentTime();
    logEntry.textContent = `[${timestamp}] ${message}`;
    
    // Add color based on type
    if (type === 'error') {
        logEntry.style.color = '#dc3545';
    } else if (type === 'warning') {
        logEntry.style.color = '#ffc107';
    } else if (type === 'success') {
        logEntry.style.color = '#28a745';
    }
    
    logContainer.appendChild(logEntry);
    logContainer.scrollTop = logContainer.scrollHeight;
}

// Convert base64 to ArrayBuffer
function base64ToArrayBuffer(base64) {
    const binaryString = window.atob(base64);
    const len = binaryString.length;
    const bytes = new Uint8Array(len);
    for (let i = 0; i < len; i++) {
        bytes[i] = binaryString.charCodeAt(i);
    }
    return bytes.buffer;
}

// Play audio chunk
function playAudioChunk(audioData) {
    // Skip audio playback if it's disabled
    if (!audioEnabled) return;
    
    try {
        const blob = new Blob([audioData], { type: 'audio/wav' });
        const url = URL.createObjectURL(blob);
        
        agentAudio.src = url;
        agentAudio.play()
            .catch(error => {
                // Handle play errors gracefully
                handleAudioError(error);
            });
        
        // Clean up URL object after playing
        agentAudio.onended = () => {
            URL.revokeObjectURL(url);
            isAgentSpeaking = false;
            updateSpeakingIndicator(false);
        };
    } catch (error) {
        // Handle any other errors in audio playback
        handleAudioError(error);
    }
}

// Get current time in HH:MM:SS format
function getCurrentTime() {
    const now = new Date();
    return now.toLocaleTimeString('en-US', {
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

// Scroll chat to bottom
function scrollToBottom() {
    chatContainer.scrollTop = chatContainer.scrollHeight;
}