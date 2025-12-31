import React, { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import Visualizer from '../components/Visualizer';

const Home = () => {
    const navigate = useNavigate();
    const [user, setUser] = useState(null);
    const [status, setStatus] = useState('Tap microphone to start (Live)');
    const [state, setState] = useState('idle'); // idle, listening, talking
    const [logs, setLogs] = useState([]);
    const [isConnected, setIsConnected] = useState(false);

    const visualizerRef = useRef(null);
    const conversationLogRef = useRef(null);

    // Audio/WS refs
    const socketRef = useRef(null);
    const audioContextRef = useRef(null);
    const streamRef = useRef(null);
    const processorRef = useRef(null);
    const sourceRef = useRef(null);
    const nextStartTimeRef = useRef(0);

    const token = localStorage.getItem('token');

    useEffect(() => {
        if (!token) {
            navigate('/login');
            return;
        }
        const storedUser = localStorage.getItem('user');
        if (storedUser) {
            setUser(JSON.parse(storedUser));
        }
    }, [token, navigate]);

    useEffect(() => {
        if (conversationLogRef.current) {
            conversationLogRef.current.scrollTop = conversationLogRef.current.scrollHeight;
        }
    }, [logs]);

    const addLog = (text) => {
        setLogs(prev => [...prev, text]);
    };

    const handleLogout = () => {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        navigate('/login');
    };

    const handleNewChat = () => {
        window.location.reload(); // Simple reset for now
    };

    const handleLoadSession = async (sessionId) => {
        if (isConnected) disconnect();

        try {
            const res = await fetch(`http://localhost:8000/api/history/${sessionId}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                const messages = await res.json();
                setLogs([]); // Clear current
                messages.forEach(msg => {
                    const role = msg.role === 'user' ? 'You' : 'Nova';
                    addLog(`${role}: ${msg.content}`);
                });
                setStatus("Viewing past session");
            }
        } catch (err) {
            console.error("Failed to load session", err);
        }
    };

    const toggleConnection = async () => {
        if (isConnected) {
            disconnect();
        } else {
            await connect();
        }
    };

    const connect = async () => {
        setStatus('Connecting...');
        try {
            streamRef.current = await navigator.mediaDevices.getUserMedia({
                audio: {
                    sampleRate: 16000,
                    channelCount: 1,
                    echoCancellation: true
                }
            });

            audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });

            const wsUrl = `ws://localhost:8000/ws/live?token=${encodeURIComponent(token)}`;
            socketRef.current = new WebSocket(wsUrl);

            socketRef.current.onopen = () => {
                console.log("WebSocket Connected");
                setIsConnected(true);
                updateUIState('listening');
                startAudioCapture();
                addLog("System: Real-time session started.");
            };

            socketRef.current.onmessage = async (event) => {
                if (typeof event.data === "string") {
                    console.log("WebSocket Message:", event.data);
                    if (event.data.startsWith("Error:")) {
                        setStatus(event.data);
                        addLog("System: " + event.data);
                    }
                    return;
                }

                if (event.data instanceof Blob) {
                    const audioData = await event.data.arrayBuffer();
                    playAudioChunk(audioData);
                } else if (event.data instanceof ArrayBuffer) {
                    playAudioChunk(event.data);
                }

                updateUIState('talking');
                setTimeout(() => {
                    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) updateUIState('listening');
                }, 500);
            };

            socketRef.current.onclose = () => {
                console.log("WebSocket Disconnected");
                disconnect();
            };

            socketRef.current.onerror = (err) => {
                console.error(err);
                setStatus("Connection Error");
            };

        } catch (err) {
            console.error(err);
            setStatus("Error: " + err.message);
        }
    };

    const disconnect = () => {
        if (socketRef.current) socketRef.current.close();
        if (streamRef.current) streamRef.current.getTracks().forEach(track => track.stop());
        if (sourceRef.current) sourceRef.current.disconnect();
        if (processorRef.current) processorRef.current.disconnect();
        if (audioContextRef.current) audioContextRef.current.close();

        setIsConnected(false);
        updateUIState('idle');
        addLog("System: Session ended.");
    };

    const startAudioCapture = () => {
        const ctx = audioContextRef.current;
        sourceRef.current = ctx.createMediaStreamSource(streamRef.current);

        // bufferSize 4096 gives ~250ms chunks at 16kHz
        processorRef.current = ctx.createScriptProcessor(4096, 1, 1);

        processorRef.current.onaudioprocess = (e) => {
            if (socketRef.current?.readyState !== WebSocket.OPEN) return;

            const inputData = e.inputBuffer.getChannelData(0);
            const pcmData = floatTo16BitPCM(inputData);

            socketRef.current.send(pcmData);

            // Visualizer
            let sum = 0;
            for (let i = 0; i < inputData.length; i++) sum += inputData[i] * inputData[i];
            const rms = Math.sqrt(sum / inputData.length);
            if (visualizerRef.current) {
                visualizerRef.current.updateVolume(rms * 100);
            }
        };

        sourceRef.current.connect(processorRef.current);
        processorRef.current.connect(ctx.destination);
    };

    const floatTo16BitPCM = (output, offset = 0) => {
        const buffer = new ArrayBuffer(output.length * 2);
        const view = new DataView(buffer);
        for (let i = 0; i < output.length; i++) {
            let s = Math.max(-1, Math.min(1, output[i]));
            s = s < 0 ? s * 0x8000 : s * 0x7FFF;
            view.setInt16(i * 2, s, true);
        }
        return buffer;
    };

    const playAudioChunk = (audioData) => {
        try {
            const int16 = new Int16Array(audioData);
            const float32 = new Float32Array(int16.length);
            for (let i = 0; i < int16.length; i++) {
                float32[i] = int16[i] / 32768.0;
            }

            const ctx = audioContextRef.current;
            const buffer = ctx.createBuffer(1, float32.length, 24000);
            buffer.getChannelData(0).set(float32);

            const source = ctx.createBufferSource();
            source.buffer = buffer;
            source.connect(ctx.destination);

            if (nextStartTimeRef.current < ctx.currentTime) {
                nextStartTimeRef.current = ctx.currentTime;
            }
            source.start(nextStartTimeRef.current);
            nextStartTimeRef.current += buffer.duration;
        } catch (e) {
            console.error("Audio playback error", e);
        }
    };

    const updateUIState = (newState) => {
        setState(newState);
        if (newState === 'listening') {
            setStatus('Listening...');
        } else if (newState === 'talking') {
            setStatus('Gemini Speaking...');
        } else {
            setStatus('Tap microphone to start (Live)');
        }
    };

    return (
        <div className="app-container">
            <div className="background-glow"></div>
            <Sidebar onNewChat={handleNewChat} onLoadSession={handleLoadSession} />

            <main className="main-content">
                <header className="top-bar">
                    <div className="header-title">Your AI Companion</div>
                    <div className="profile-section">
                        <div className="profile-pic" id="profile-pic">
                            {user?.picture ? (
                                <img src={user.picture} alt="Profile" />
                            ) : (
                                <span>{user?.name?.charAt(0).toUpperCase() || 'U'}</span>
                            )}
                        </div>
                        <div className="profile-dropdown" id="profile-dropdown">
                            <button id="logout-btn" onClick={handleLogout}>Logout</button>
                        </div>
                    </div>
                </header>

                <div className="assistant-interface">
                    <Visualizer ref={visualizerRef} state={state} />

                    <div id="status-text" className="status">{status}</div>

                    <div className="controls">
                        <button
                            id="mic-btn"
                            className="mic-button"
                            onClick={toggleConnection}
                            style={state === 'listening' ? { background: 'var(--accent-color)', color: '#000' } : {}}
                        >
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                                <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z" />
                                <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
                            </svg>
                        </button>
                    </div>
                </div>

                <div id="conversation-log" className="conversation-log" ref={conversationLogRef}>
                    {logs.map((log, index) => (
                        <div key={index} style={{ marginBottom: "10px" }}>{log}</div>
                    ))}
                </div>
            </main>
        </div>
    );
};

export default Home;
