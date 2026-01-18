const micBtn = document.getElementById('mic-btn');
const visualizer = document.getElementById('visualizer');
const statusText = document.getElementById('status-text');
const conversationLog = document.getElementById('conversation-log');
const logoutBtn = document.getElementById('logout-btn');
const historyList = document.getElementById('history-list');
const newChatBtn = document.getElementById('new-chat-btn');
const profilePic = document.getElementById('profile-pic');

// API Configuration
const API_URL = window.location.hostname === 'localhost' 
    ? 'http://localhost:8000' 
    : window.location.origin.replace(/^http/, 'http').replace(/web-/, 'api-');

// Auth Check
const token = localStorage.getItem('token');
const user = JSON.parse(localStorage.getItem('user'));

if (!token) {
    window.location.href = 'login.html';
}

if (user && user.picture) {
    profilePic.innerHTML = `<img src="${user.picture}" alt="Profile" onerror="this.parentElement.innerHTML='<span>${(user.name || 'U').charAt(0).toUpperCase()}</span>'">`;
} else if (user && user.name) {
    profilePic.innerHTML = `<span>${user.name.charAt(0).toUpperCase()}</span>`;
}

if (logoutBtn) {
    logoutBtn.addEventListener('click', () => {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = 'login.html';
    });
}

// Sidebar Logic
newChatBtn.addEventListener('click', () => {
    // Refresh to start clean state or reset variables
    window.location.reload();
});

async function loadHistory() {
    try {
        const res = await fetch(`${API_URL}/api/history`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.ok) {
            const sessions = await res.json();
            renderHistory(sessions);
        }
    } catch (err) {
        console.error("Failed to load history", err);
    }
}

function renderHistory(sessions) {
    historyList.innerHTML = '';
    sessions.forEach(session => {
        const div = document.createElement('div');
        div.className = 'history-item';
        div.textContent = session.title || `Session ${session.id}`;
        div.onclick = () => loadSession(session.id);
        historyList.appendChild(div);
    });
}

function addLog(text) {
    const p = document.createElement('div'); // Changed to div for styling flexibility
    p.style.marginBottom = "10px";
    p.textContent = text;
    conversationLog.appendChild(p);
    conversationLog.scrollTop = conversationLog.scrollHeight;
}

// Load history on start
loadHistory();

// System State
let isConnected = false;
let socket;
let audioContext;
let processor;
let source;
let stream;
let nextStartTime = 0;

micBtn.addEventListener('click', toggleConnection);

async function loadSession(sessionId) {
    // Stop any active connection logic if needed
    if (isConnected) disconnect();
    
    try {
        const res = await fetch(`http://localhost:8000/api/history/${sessionId}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.ok) {
            const messages = await res.json();
            conversationLog.innerHTML = ''; // Clear current
            messages.forEach(msg => {
                const role = msg.role === 'user' ? 'You' : 'Nova';
                addLog(`${role}: ${msg.content}`);
            });
            statusText.textContent = "Viewing past session";
        }
    } catch (err) {
        console.error("Failed to load session", err);
    }
}

async function toggleConnection() {
    if (isConnected) {
        disconnect();
    } else {
        await connect();
    }
}

async function connect() {
    statusText.textContent = 'Connecting...';
    try {
        // 1. Setup Audio Input (16kHz PCM is standard for speech)
        stream = await navigator.mediaDevices.getUserMedia({ 
            audio: {
                sampleRate: 16000, 
                channelCount: 1,
                echoCancellation: true
            } 
        });

        audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
        
        // 2. Setup WebSocket
        // Connect to the WS endpoint
        const wsUrl = `ws://localhost:8000/ws/live?token=${encodeURIComponent(token)}`;
        socket = new WebSocket(wsUrl);
        
        socket.onopen = () => {
            console.log("WebSocket Connected");
            isConnected = true;
            updateUIState('listening');
            startAudioCapture();
            addLog("System: Real-time session started.");
        };

        socket.onmessage = async (event) => {
            if (typeof event.data === "string") {
                console.log("WebSocket Message:", event.data);
                if (event.data.startsWith("Error:")) {
                    statusText.textContent = event.data;
                    addLog("System: " + event.data);
                }
                return;
            }
            
            // Received audio blob from server
            if (event.data instanceof Blob) {
                 const audioData = await event.data.arrayBuffer();
                 playAudioChunk(audioData);
            } else if (event.data instanceof ArrayBuffer) {
                 playAudioChunk(event.data);
            }
            
            updateUIState('talking');
             // Reset to listening state after a bit if needed, or visualizer handles it
             setTimeout(() => {
                 if(isConnected) updateUIState('listening');
             }, 500); 
        };

        socket.onclose = () => {
            console.log("WebSocket Disconnected");
            disconnect();
        };

        socket.onerror = (err) => {
            console.error(err);
            statusText.textContent = "Connection Error";
        };

    } catch (err) {
        console.error(err);
        statusText.textContent = "Error: " + err.message;
    }
}

function disconnect() {
    if (socket) socket.close();
    if (stream) stream.getTracks().forEach(track => track.stop());
    if (source) source.disconnect();
    if (processor) processor.disconnect();
    if (audioContext) audioContext.close();
    
    isConnected = false;
    updateUIState('idle');
    addLog("System: Session ended.");
}

function startAudioCapture() {
     source = audioContext.createMediaStreamSource(stream);
     
     // Use ScriptProcessor for simplicity (AudioWorklet is better but needs separate file)
     // bufferSize 4096 gives ~250ms chunks at 16kHz
     processor = audioContext.createScriptProcessor(4096, 1, 1);
     
     processor.onaudioprocess = (e) => {
         if (!isConnected) return;
         
         const inputData = e.inputBuffer.getChannelData(0);
         // Convert float32 to int16 PCM
         const pcmData = floatTo16BitPCM(inputData);
         
         if (socket.readyState === WebSocket.OPEN) {
             socket.send(pcmData);
         }
         
         // Visualizer
         let sum = 0;
         for(let i=0; i<inputData.length; i++) sum += inputData[i] * inputData[i];
         const rms = Math.sqrt(sum / inputData.length);
         updateVisualizer(rms * 100);
     };
     
     source.connect(processor);
     processor.connect(audioContext.destination);
}

function floatTo16BitPCM(output, offset=0) {
    const buffer = new ArrayBuffer(output.length * 2);
    const view = new DataView(buffer);
    for (let i = 0; i < output.length; i++) {
        let s = Math.max(-1, Math.min(1, output[i]));
        s = s < 0 ? s * 0x8000 : s * 0x7FFF;
        view.setInt16(i * 2, s, true); // little-endian
    }
    return buffer;
}

function playAudioChunk(audioData) {
    // Gemini Live sends back raw PCM, typically 24kHz.
    // If we simply play it as is through 16kHz context, it might sound slow/fast.
    // Let's decode it as Int16.
    
    try {
        const int16 = new Int16Array(audioData);
        const float32 = new Float32Array(int16.length);
        for (let i=0; i<int16.length; i++) {
            float32[i] = int16[i] / 32768.0;
        }
        
        // Gemini usually sends 24000Hz.
        const buffer = audioContext.createBuffer(1, float32.length, 24000);
        buffer.getChannelData(0).set(float32);
        
        const source = audioContext.createBufferSource();
        source.buffer = buffer;
        source.connect(audioContext.destination);
        
        // Schedule for seamless playback
        if (nextStartTime < audioContext.currentTime) {
            nextStartTime = audioContext.currentTime;
        }
        source.start(nextStartTime);
        nextStartTime += buffer.duration;
    } catch (e) {
        console.error("Audio playback error", e);
    }
}

function updateVisualizer(volume) {
    const scale = 1 + (volume / 2); // Adjust sensitivity
    const circles = visualizer.querySelectorAll('.circle');
    circles.forEach(c => c.style.transform = `scale(${scale})`);
}

function updateUIState(state) {
    visualizer.className = 'visualizer';
    if (state === 'listening') {
        visualizer.classList.add('listening');
        statusText.textContent = 'Listening...';
        micBtn.style.background = 'var(--accent-color)';
        micBtn.style.color = '#000';
    } else if (state === 'talking') {
        visualizer.classList.add('talking');
        statusText.textContent = 'Gemini Speaking...';
    } else {
        statusText.textContent = 'Tap microphone to start (Live)';
        micBtn.style.background = '';
        micBtn.style.color = '';
    }
}
