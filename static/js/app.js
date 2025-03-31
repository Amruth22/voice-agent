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
let audioContext = null;
let audioProcessor = null;
let audioSource = null;
let userAudioStream = null;
let isCapturingAudio = false;
let audioQueue = [];
let isPlayingAudio = false;
let selectedOutputDevice = 'default';

// Initialize the page
document.addEventListener('DOMContentLoaded', () => {
    // Load audio devices
    loadAudioDevices();
    
    // Set up event listeners
    setupEventListeners();
    
    // Check if browser supports getUserMedia
    checkBrowserSupport();
    
    // Add notice about Ngrok deployment
    addNgrokNotice();
});

// Add notice about Ngrok deployment
function addNgrokNotice() {
    // Check if we're running on Ngrok by looking at the hostname
    const isNgrok = window.location.hostname.includes('ngrok');
    
    if (isNgrok) {
        const noticeElement = document.createElement('div');
        noticeElement.className = 'alert alert-info mb-3';
        noticeElement.innerHTML = `
            <strong>Remote Access Mode:</strong> This application is running on a remote server.
            You will need to grant microphone permission to use voice features.
            Audio will be processed on the remote server but played through your local speakers.
        `;
        chatContainer.prepend(noticeElement);
        
        addLogEntry('Running in remote access mode via Ngrok', 'info');
    }
}

// Check if browser supports getUserMedia and AudioContext
function checkBrowserSupport() {
    let supportMessage = '';
    let supportType = 'info';
    
    // Check microphone support
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        supportMessage += 'Your browser does not support microphone access. ';
        supportType = 'warning';
        micToggle.disabled = true;
        micToggle.checked = false;
    } else {
        supportMessage += 'Microphone access supported. ';
    }
    
    // Check AudioContext support
    if (!window.AudioContext && !window.webkitAudioContext) {
        supportMessage += 'Your browser does not support AudioContext. Audio processing may be limited. ';
        supportType = 'warning';
    } else {
        supportMessage += 'Audio processing supported. ';
    }
    
    // Check audio output selection support
    if (typeof HTMLAudioElement.prototype.setSinkId !== 'function') {
        supportMessage += 'Your browser does not support audio output selection. Default speakers will be used.';
        supportType = 'warning';
        outputDeviceSelect.disabled = true;
    } else {
        supportMessage += 'Audio output selection supported.';
    }
    
    addLogEntry(supportMessage, supportType);
}

// Request access to user's microphone
function requestUserMicrophone() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        addLogEntry('Microphone access not supported by your browser', 'error');
        return Promise.reject(new Error('getUserMedia not supported'));
    }
    
    return navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
            addLogEntry('Microphone access granted', 'success');
            userAudioStream = stream;
            return stream;
        })
        .catch(error => {
            addLogEntry(`Microphone access denied: ${error.message}`, 'error');
            micToggle.checked = false;
            throw error;
        });
}

// Start capturing audio from user's microphone
function startAudioCapture() {
    if (!userAudioStream) {
        addLogEntry('No microphone access. Please enable microphone first.', 'error');
        return false;
    }
    
    if (isCapturingAudio) {
        return true; // Already capturing
    }
    
    try {
        // Create audio context
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
        audioSource = audioContext.createMediaStreamSource(userAudioStream);
        
        // Create script processor for audio processing
        audioProcessor = audioContext.createScriptProcessor(4096, 1, 1);
        
        // Process audio data
        audioProcessor.onaudioprocess = function(e) {
            if (!isAgentRunning || !micToggle.checked) return;
            
            // Get audio data from microphone
            const inputData = e.inputBuffer.getChannelData(0);
            
            // Convert to 16-bit PCM (format expected by Deepgram)
            const pcmData = new Int16Array(inputData.length);
            for (let i = 0; i < inputData.length; i++) {
                pcmData[i] = Math.max(-1, Math.min(1, inputData[i])) * 0x7FFF;
            }
            
            // Send to server
            const buffer = pcmData.buffer;
            const base64data = arrayBufferToBase64(buffer);
            socket.emit('audio_data', { audio: base64data });
        };
        
        // Connect nodes
        audioSource.connect(audioProcessor);
        audioProcessor.connect(audioContext.destination);
        
        isCapturingAudio = true;
        addLogEntry('Started capturing audio from your microphone', 'success');
        return true;
    } catch (error) {
        addLogEntry(`Error starting audio capture: ${error.message}`, 'error');
        return false;
    }
}

// Stop capturing audio
function stopAudioCapture() {
    if (!isCapturingAudio) return;
    
    try {
        if (audioProcessor) {
            audioProcessor.disconnect();
            audioProcessor = null;
        }
        
        if (audioSource) {
            audioSource.disconnect();
            audioSource = null;
        }
        
        if (audioContext && audioContext.state !== 'closed') {
            audioContext.close().catch(e => console.error('Error closing audio context:', e));
            audioContext = null;
        }
        
        isCapturingAudio = false;
        addLogEntry('Stopped capturing audio from your microphone');
    } catch (error) {
        addLogEntry(`Error stopping audio capture: ${error.message}`, 'error');
    }
}

// Load available audio devices
function loadAudioDevices() {
    if (navigator.mediaDevices && navigator.mediaDevices.enumerateDevices) {
        navigator.mediaDevices.enumerateDevices()
            .then(devices => {
                // Clear existing options
                inputDeviceSelect.innerHTML = '';
                outputDeviceSelect.innerHTML = '';
                
                // Add default option
                const defaultInputOption = document.createElement('option');
                defaultInputOption.value = 'default';
                defaultInputOption.textContent = 'Default Microphone';
                inputDeviceSelect.appendChild(defaultInputOption);
                
                const defaultOutputOption = document.createElement('option');
                defaultOutputOption.value = 'default';
                defaultOutputOption.textContent = 'Default Speaker';
                outputDeviceSelect.appendChild(defaultOutputOption);
                
                // Add input devices
                const audioInputDevices = devices.filter(device => device.kind === 'audioinput');
                audioInputDevices.forEach(device => {
                    const option = document.createElement('option');
                    option.value = device.deviceId;
                    option.textContent = device.label || `Microphone ${inputDeviceSelect.options.length}`;
                    inputDeviceSelect.appendChild(option);
                });
                
                // Add output devices
                const audioOutputDevices = devices.filter(device => device.kind === 'audiooutput');
                audioOutputDevices.forEach(device => {
                    const option = document.createElement('option');
                    option.value = device.deviceId;
                    option.textContent = device.label || `Speaker ${outputDeviceSelect.options.length}`;
                    outputDeviceSelect.appendChild(option);
                });
                
                // If no labels are available, it means permission hasn't been granted yet
                if (audioInputDevices.length > 0 && !audioInputDevices[0].label) {
                    addLogEntry('Grant microphone permission to see device names', 'warning');
                } else {
                    addLogEntry('Audio devices loaded from browser');
                }
                
                // Check if output selection is supported
                if (typeof HTMLAudioElement.prototype.setSinkId !== 'function') {
                    outputDeviceSelect.disabled = true;
                    addLogEntry('Your browser does not support audio output selection', 'warning');
                }
            })
            .catch(error => {
                addLogEntry(`Error enumerating audio devices: ${error.message}`, 'error');
                
                // Add default options
                inputDeviceSelect.innerHTML = '<option value="default">Default Microphone</option>';
                outputDeviceSelect.innerHTML = '<option value="default">Default Speaker</option>';
            });
    } else {
        // Browser doesn't support enumerateDevices
        inputDeviceSelect.innerHTML = '<option value="default">Default Microphone</option>';
        outputDeviceSelect.innerHTML = '<option value="default">Default Speaker</option>';
        addLogEntry('Your browser does not support device enumeration', 'warning');
    }
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
        if (micToggle.checked) {
            // Request microphone access and start capturing
            requestUserMicrophone()
                .then(() => {
                    startAudioCapture();
                })
                .catch(() => {
                    micToggle.checked = false;
                });
        } else {
            // Stop capturing audio
            stopAudioCapture();
        }
        
        addLogEntry(`Microphone ${micToggle.checked ? 'enabled' : 'disabled'}`);
    });
    
    // Output device selection
    outputDeviceSelect.addEventListener('change', () => {
        selectedOutputDevice = outputDeviceSelect.value;
        
        // Try to set the audio output device if supported
        if (typeof agentAudio.setSinkId === 'function') {
            agentAudio.setSinkId(selectedOutputDevice)
                .then(() => {
                    addLogEntry(`Audio output set to: ${outputDeviceSelect.options[outputDeviceSelect.selectedIndex].text}`, 'success');
                })
                .catch(error => {
                    addLogEntry(`Error setting audio output: ${error.message}`, 'error');
                });
        }
    });
    
    // Socket.IO event listeners
    setupSocketListeners();
    
    // Audio element events
    agentAudio.addEventListener('ended', () => {
        isAgentSpeaking = false;
        updateSpeakingIndicator(false);
        
        // Play next audio in queue if any
        playNextAudioInQueue();
    });
    
    agentAudio.addEventListener('error', (e) => {
        addLogEntry(`Audio playback error: ${e.target.error.message || 'Unknown error'}`, 'error');
        isAgentSpeaking = false;
        updateSpeakingIndicator(false);
        
        // Try to play next audio in queue
        playNextAudioInQueue();
    });
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
        
        // Add audio to queue and play
        const audioData = base64ToArrayBuffer(data.audio);
        queueAudioForPlayback(audioData);
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
    
    // Connection events
    socket.on('connect', () => {
        addLogEntry('Connected to server', 'success');
    });
    
    socket.on('disconnect', () => {
        addLogEntry('Disconnected from server', 'warning');
        isAgentRunning = false;
        startButton.disabled = false;
        stopButton.disabled = true;
    });
    
    socket.on('connect_error', (error) => {
        addLogEntry(`Connection error: ${error.message}`, 'error');
    });
}

// Queue audio for playback
function queueAudioForPlayback(audioData) {
    audioQueue.push(audioData);
    
    // If not currently playing, start playback
    if (!isPlayingAudio) {
        playNextAudioInQueue();
    }
}

// Play next audio in queue
function playNextAudioInQueue() {
    if (audioQueue.length === 0) {
        isPlayingAudio = false;
        return;
    }
    
    isPlayingAudio = true;
    const audioData = audioQueue.shift();
    playAudioChunk(audioData);
}

// Start the voice agent
function startVoiceAgent() {
    // If microphone is enabled, request access
    if (micToggle.checked && !userAudioStream) {
        requestUserMicrophone()
            .then(() => {
                startAudioCapture();
            })
            .catch(() => {
                micToggle.checked = false;
            });
    }
    
    const inputDeviceId = inputDeviceSelect.value;
    selectedOutputDevice = outputDeviceSelect.value;
    
    // Try to set the audio output device if supported
    if (typeof agentAudio.setSinkId === 'function') {
        agentAudio.setSinkId(selectedOutputDevice)
            .then(() => {
                addLogEntry(`Audio output set to: ${outputDeviceSelect.options[outputDeviceSelect.selectedIndex].text}`, 'success');
            })
            .catch(error => {
                addLogEntry(`Error setting audio output: ${error.message}`, 'error');
            });
    }
    
    socket.emit('start_voice_agent', {
        inputDeviceId,
        outputDeviceId: selectedOutputDevice
    });
    
    isAgentRunning = true;
    startButton.disabled = true;
    stopButton.disabled = false;
    
    addLogEntry('Voice agent started');
}

// Stop the voice agent
function stopVoiceAgent() {
    socket.emit('stop_voice_agent');
    
    // Stop audio capture
    stopAudioCapture();
    
    // Clear audio queue
    audioQueue = [];
    isPlayingAudio = false;
    
    isAgentRunning = false;
    isAgentSpeaking = false;
    startButton.disabled = false;
    stopButton.disabled = true;
    micToggle.checked = false;
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
    
    // Add speaking indicator if agent is speaking
    if (isAgentSpeaking) {
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

// Convert ArrayBuffer to base64
function arrayBufferToBase64(buffer) {
    let binary = '';
    const bytes = new Uint8Array(buffer);
    const len = bytes.byteLength;
    for (let i = 0; i < len; i++) {
        binary += String.fromCharCode(bytes[i]);
    }
    return window.btoa(binary);
}

// Play audio chunk
function playAudioChunk(audioData) {
    try {
        const blob = new Blob([audioData], { type: 'audio/wav' });
        const url = URL.createObjectURL(blob);
        
        // Set the source and play
        agentAudio.src = url;
        
        // Try to set the audio output device if supported
        if (typeof agentAudio.setSinkId === 'function' && selectedOutputDevice) {
            agentAudio.setSinkId(selectedOutputDevice)
                .then(() => {
                    return agentAudio.play();
                })
                .catch(error => {
                    addLogEntry(`Error setting audio output: ${error.message}`, 'error');
                    return agentAudio.play();
                });
        } else {
            // Just play with default output
            agentAudio.play()
                .catch(error => {
                    addLogEntry(`Error playing audio: ${error.message}`, 'error');
                    
                    // Try to play next audio in queue
                    playNextAudioInQueue();
                });
        }
        
        // Clean up URL object after playing
        agentAudio.onended = () => {
            URL.revokeObjectURL(url);
            isAgentSpeaking = false;
            updateSpeakingIndicator(false);
            
            // Play next audio in queue
            playNextAudioInQueue();
        };
    } catch (error) {
        addLogEntry(`Error preparing audio: ${error.message}`, 'error');
        
        // Try to play next audio in queue
        playNextAudioInQueue();
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