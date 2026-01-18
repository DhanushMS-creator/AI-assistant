import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const Login = () => {
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    // Callback handled inside initCodeClient now

    // Initialize Google OAuth2 Client
    const initGoogle = () => {
      if (window.google?.accounts) {
        // We use initCodeClient for Authorization Code Flow (needed for Calendar scopes)
        const client = window.google.accounts.oauth2.initCodeClient({
          client_id: "85725976781-jikri2iuo1odlqasejb7ffll9ldkvdc6.apps.googleusercontent.com",
          scope: "https://www.googleapis.com/auth/calendar https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/userinfo.email openid",
          ux_mode: "popup",
          callback: async (response) => {
            if (response.code) {
              setError("Authorizing...");
              try {
                // Send 'code' as 'credential' parameter to reuse existing backend endpoint structure
                const res = await fetch(`${API_URL}/api/auth/google-login`, {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ credential: response.code })
                });

                if (!res.ok) throw new Error("Login failed");

                const data = await res.json();
                localStorage.setItem('token', data.access_token);
                localStorage.setItem('user', JSON.stringify(data.user));
                navigate('/');
              } catch (err) {
                console.error(err);
                setError("Login Failed. Please try again.");
              }
            }
          },
        });

        // Render a custom button that triggers the client
        const btnParent = document.getElementById("google-login-btn");
        if (btnParent) {
          // Clear previous content
          btnParent.innerHTML = '';

          const button = document.createElement("button");
          button.innerText = "Sign in with Google";
          button.style.backgroundColor = "white";
          button.style.color = "black";
          button.style.border = "none";
          button.style.padding = "10px 20px";
          button.style.borderRadius = "20px";
          button.style.fontSize = "16px";
          button.style.fontWeight = "bold";
          button.style.cursor = "pointer";
          button.style.display = "flex";
          button.style.alignItems = "center";
          button.style.gap = "10px";

          // Add Google Icon
          const icon = document.createElement("img");
          icon.src = "https://upload.wikimedia.org/wikipedia/commons/5/53/Google_%22G%22_Logo.svg";
          icon.style.width = "20px";
          button.prepend(icon);

          button.onclick = () => client.requestCode();
          btnParent.appendChild(button);
        }
      }
    }

    // Check if script is already loaded
    if (window.google?.accounts) {
      initGoogle();
    } else {
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
