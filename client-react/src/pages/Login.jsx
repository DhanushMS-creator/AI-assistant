import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

const Login = () => {
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    // Define the callback function globally so Google script can call it
    window.handleCredentialResponse = async (response) => {
      setError("Verifying...");
      
      try {
        const res = await fetch('http://localhost:8000/api/auth/google-login', {
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
  }, [navigate]);

  return (
    <div className="container" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
       <div className="background-glow"></div>
        <div className="assistant-interface"> 
            <header>
                <h1>Nova</h1>
                <p>Login to continue</p>
            </header>

            <div style={{ marginTop: '30px' }}>
                <div id="g_id_onload"
                     data-client_id="85725976781-jikri2iuo1odlqasejb7ffll9ldkvdc6.apps.googleusercontent.com"
                     data-callback="handleCredentialResponse"
                     data-auto_prompt="false">
                </div>
                <div className="g_id_signin"
                     data-type="standard"
                     data-size="large"
                     data-theme="filled_black"
                     data-text="sign_in_with"
                     data-shape="pill"
                     data-logo_alignment="left">
                </div>
            </div>

            {error && <p id="error-msg" style={{ color: '#ff4444', marginTop: '15px', fontSize: '0.9em' }}>{error}</p>}
        </div>
    </div>
  );
};

export default Login;
