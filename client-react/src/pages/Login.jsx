import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || "85725976781-jikri2iuo1odlqasejb7ffll9ldkvdc6.apps.googleusercontent.com";

const Login = () => {
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    // Define the callback function globally so Google script can call it
    window.handleCredentialResponse = async (response) => {
      setError("Verifying...");

      try {
        const res = await fetch(`${API_URL}/api/auth/google-login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ credential: response.credential })
        });

        if (!res.ok) {
          throw new Error("Login failed");
        }

        const data = await res.json();

        localStorage.setItem('token', data.access_token);
        localStorage.setItem('user', JSON.stringify(data.user)); // Store user info

        navigate('/');
      } catch (err) {
        console.error(err);
        setError("Login Failed. Please try again.");
      }
    };

    // Initialize Google Button
    const initGoogle = () => {
      if (window.google?.accounts) {
        window.google.accounts.id.initialize({
          client_id: GOOGLE_CLIENT_ID,
          callback: window.handleCredentialResponse,
          auto_select: false,
          cancel_on_tap_outside: false
        });

        const btnParent = document.getElementById("google-login-btn");
        if (btnParent) {
          window.google.accounts.id.renderButton(
            btnParent,
            { theme: "filled_black", size: "large", shape: "pill", type: "standard" }
          );
        }
      }
    }

    // Check if script is already loaded
    if (window.google?.accounts) {
      initGoogle();
    } else {
      // If not, wait for it (though index.html loads it, timing varies)
      const checkGoogle = setInterval(() => {
        if (window.google?.accounts) {
          clearInterval(checkGoogle);
          initGoogle();
        }
      }, 100);
    }
  }, [navigate]);

  return (
    <div className="container" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
      <div className="background-glow"></div>
      <div className="assistant-interface">
        <header>
          <h1>Nova</h1>
          <p>Login to continue</p>
        </header>

        <div style={{ marginTop: '30px', height: '50px' }}>
          {/* Container for the button */}
          <div id="google-login-btn"></div>
        </div>

        {error && <p id="error-msg" style={{ color: '#ff4444', marginTop: '15px', fontSize: '0.9em' }}>{error}</p>}
      </div>
    </div>
  );
};

export default Login;
