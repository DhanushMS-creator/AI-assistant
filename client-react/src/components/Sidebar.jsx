import React, { useEffect, useState } from 'react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const Sidebar = ({ onNewChat, onLoadSession }) => {
    const [sessions, setSessions] = useState([]);

    useEffect(() => {
        loadHistory();
    }, []);

    const loadHistory = async () => {
        const token = localStorage.getItem('token');
        try {
            const res = await fetch(`${API_URL}/api/history`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setSessions(data);
            }
        } catch (err) {
            console.error("Failed to load history", err);
        }
    };

    return (
        <aside className="sidebar">
            <div className="logo">
                <h2>NOVA</h2>
            </div>
            <div className="new-chat-container">
                <button id="new-chat-btn" className="new-chat-btn" onClick={onNewChat}>+ New Chat</button>
            </div>
            <div className="history-list" id="history-list">
                {sessions.map(session => (
                    <div
                        key={session.id}
                        className="history-item"
                        onClick={() => onLoadSession(session.id)}
                    >
                        {session.title || `Session ${session.id}`}
                    </div>
                ))}
            </div>
        </aside>
    );
};

export default Sidebar;
