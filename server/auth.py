from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from google.oauth2 import id_token
from google.auth.transport import requests
import os

# SECRET_KEY for signing local JWTs (in prod, use a strong random string)
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 300

from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# ... existing code ...

def verify_google_token(token: str):
    # Backward compatibility if needed, but we are switching to Auth Code flow primarily
    try:
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        id_info = id_token.verify_oauth2_token(token, requests.Request(), client_id)
        return id_info
    except Exception as e:
        print(f"Token verification failed: {e}")
        return None

import json

# ... existing code ...

def exchange_code_for_credentials(auth_code: str):
    try:
        # 1. Try explicit Env Vars
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        
        # 2. Smart Fallback: Check GOOGLE_APPLICATION_CREDENTIALS if secret is missing
        # (Users sometimes paste the OAuth JSON there)
        if not client_secret:
            gac = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            if gac:
                try:
                    data = None
                    if gac.strip().startswith("{"):
                        data = json.loads(gac)
                    elif os.path.exists(gac):
                        with open(gac) as f:
                            data = json.load(f)
                    
                    if data:
                        web_config = data.get("web") or data.get("installed")
                        if web_config:
                            if not client_secret:
                                client_secret = web_config.get("client_secret")
                            if not client_id: # Also fallback ID just in case
                                client_id = web_config.get("client_id")
                except Exception as parse_err:
                    print(f"Failed to parse credentials fallback: {parse_err}")

        # Create the flow using the client secrets
        client_config = {
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        }
        
        # Scopes must match what frontend requests
        scopes = [
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile",
            "https://www.googleapis.com/auth/calendar",
            "openid"
        ]
        
        flow = Flow.from_client_config(
            client_config,
            scopes=scopes,
            redirect_uri="postmessage" # Important for React SPA
        )
        
        flow.fetch_token(code=auth_code)
        credentials = flow.credentials
        
        # Get user info using the credentials
        id_info = id_token.verify_oauth2_token(
            credentials.id_token, 
            requests.Request(), 
            client_id
        )
        
        return {
            "email": id_info.get("email"),
            "sub": id_info.get("sub"),
            "name": id_info.get("name"),
            "picture": id_info.get("picture"),
            "refresh_token": credentials.refresh_token,
            "access_token": credentials.token # Can be used temporarily
        }
    except Exception as e:
        print(f"Auth Code Exchange Failed: {e}")
        return None

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
