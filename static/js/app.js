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

// State variables
let isAgentRunning = false;
let typingIndicator = null;

// Initialize the page
document.addEventListener('DOMContentLoaded', () => {
    // Load audio devices
    loadAudioDevices();
    
    // Set up event listeners
    setupEventListeners();
    
    // Add Vercel deployment notice
    addLogEntry('Running on Vercel deployment (limited functionality)');
    addLogEntry('Microphone functionality is disabled in this version');
});

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
            
            addLogEntry('Audio devices loaded (mock devices for Vercel)');
            
            // Disable microphone toggle in Vercel deployment
            micToggle.disabled = true;
            micToggle.checked = false;
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
    
    // Socket.IO event listeners
    setupSocketListeners();
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
    
    // Typing indicator
    socket.on('typing_indicator', (data) => {
        if (data.typing) {
            showTypingIndicator();
        } else {
            removeTypingIndicator();
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
    socket.emit('start_voice_agent');
    
    isAgentRunning = true;
    startButton.disabled = true;
    stopButton.disabled = false;
    
    addLogEntry('Voice agent started (text-only mode for Vercel)');
}

// Stop the voice agent
function stopVoiceAgent() {
    socket.emit('stop_voice_agent');
    
    isAgentRunning = false;
    startButton.disabled = false;
    stopButton.disabled = true;
    
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
    contentElement.textContent = message;
    
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
    
    addLogEntry(`Appointment scheduled for ${customer.name} on ${formattedTime}`);
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