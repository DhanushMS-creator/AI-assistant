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

def verify_google_token(token: str):
    try:
        # We specify the client ID to verify the audience
        # user need to put their client id in .env or we can pass None to skip audience check (less secure)
        # For this demo, we'll try to get audience from .env
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        
        id_info = id_token.verify_oauth2_token(token, requests.Request(), client_id)
        return id_info
    except ValueError as e:
        print(f"Token verification failed: {e}")
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
