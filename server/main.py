from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, Header, status, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from .services.model_handler import model_handler
from .services.voice_handler import voice_handler
from .services.live_handler import live_handler
from .database import engine, Base, get_db
from .models import User, Session as ChatSession, Message
from .auth import verify_google_token, create_access_token, decode_access_token
import base64
from typing import List, Optional

# Create Database Tables
Base.metadata.create_all(bind=engine)

app = FastAPI()

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[int] = None

class TTSRequest(BaseModel):
    text: str

class GoogleLoginRequest(BaseModel):
    credential: str

# Dependency to get current user
async def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization Header")
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != 'bearer':
            raise HTTPException(status_code=401, detail="Invalid Authentication Scheme")
            
        payload = decode_access_token(token)
        if payload is None:
            raise HTTPException(status_code=401, detail="Invalid Token")
            
        user_email = payload.get("sub")
        if user_email is None:
            raise HTTPException(status_code=401, detail="Invalid Token Payload")
            
        user = db.query(User).filter(User.email == user_email).first()
        if user is None:
             raise HTTPException(status_code=401, detail="User not found")
        
        return user
    except Exception as e:
        print(e)
        raise HTTPException(status_code=401, detail="Authentication Failed")


@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Personal Assistant Backend is running"}

@app.post("/api/auth/google-login")
async def google_login(request: GoogleLoginRequest, db: Session = Depends(get_db)):
    # Try exchanging code first (New Flow)
    google_data = None
    
    # If credential looks long (JWT), it's old flow. If short/opaque, it might be a code? 
    # Actually, let's assume 'credential' field now carries the 'code' from frontend
    # because we will change frontend to send {CodeResponse.code} as 'credential' or similar.
    # To be safe, we try code exchange.
    
    if request.credential.startswith("4/"): # Auth codes usually start with 4/
         from .auth import exchange_code_for_credentials
         google_data = exchange_code_for_credentials(request.credential)
    else:
         # Fallback to old JWT verification (for existing sessions or simple login)
         google_data = verify_google_token(request.credential)

    if not google_data:
        raise HTTPException(status_code=400, detail="Invalid Google Token or Code")
    
    email = google_data.get('email')
    google_id = google_data.get('sub')
    name = google_data.get('name')
    picture = google_data.get('picture')
    refresh_token = google_data.get('refresh_token')

    # Check if user exists
    user = db.query(User).filter(User.email == email).first()
    if not user:
        # Create new user
        user = User(email=email, google_id=google_id, name=name, profile_pic=picture, refresh_token=refresh_token)
        db.add(user)
    else:
        # Update details if changed and SAVE REFRESH TOKEN if we got a new one
        user.name = name
        user.profile_pic = picture
        if refresh_token:
            user.refresh_token = refresh_token
    
    db.commit()
    db.refresh(user)
    
    # Create JWT
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer", "user": {"name": user.name, "picture": user.profile_pic}}

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not request.message:
        raise HTTPException(status_code=400, detail="Message is empty")
    
    # Generate AI Response
    response_text = await model_handler.generate_response(request.message, user=current_user)

    # Persistence Logic
    session_id = request.session_id
    if not session_id:
        # Create new session if none provided
        new_session = ChatSession(user_id=current_user.id, title=request.message[:30] + "...")
        db.add(new_session)
        db.commit()
        db.refresh(new_session)
        session_id = new_session.id
    
    # Check if session belongs to user
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == current_user.id).first()
    if not session:
         raise HTTPException(status_code=404, detail="Session not found or access denied")

    # Save User Message
    user_msg = Message(session_id=session_id, role="user", content=request.message)
    db.add(user_msg)

    # Save AI Message
    ai_msg = Message(session_id=session_id, role="model", content=response_text)
    db.add(ai_msg)
    
    db.commit()

    return {"response": response_text, "session_id": session_id}

@app.get("/api/history")
async def get_chat_history(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    sessions = db.query(ChatSession).filter(ChatSession.user_id == current_user.id).order_by(ChatSession.created_at.desc()).all()
    return [{"id": s.id, "title": s.title, "created_at": s.created_at} for s in sessions]

@app.get("/api/history/{session_id}")
async def get_session_messages(session_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    messages = db.query(Message).filter(Message.session_id == session_id).order_by(Message.created_at.asc()).all()
    return [{"role": m.role, "content": m.content, "created_at": m.created_at} for m in messages]

@app.post("/api/speech/stt")
async def stt_endpoint(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    audio_content = await file.read()
    text = await voice_handler.speech_to_text(audio_content)
    return {"transcript": text}

@app.post("/api/speech/tts")
async def tts_endpoint(request: TTSRequest, current_user: User = Depends(get_current_user)):
    audio_content = await voice_handler.text_to_speech(request.text)
    if not audio_content:
        raise HTTPException(status_code=500, detail="TTS Generation failed")
    
    return {"audio": base64.b64encode(audio_content).decode('utf-8')}

# WebSocket Endpoint for Live
@app.websocket("/ws/live")
async def live_endpoint(websocket: WebSocket, db: Session = Depends(get_db)):
    await websocket.accept()
    
    token = websocket.query_params.get("token")
    user = None
    if token:
        try:
            payload = decode_access_token(token)
            if payload:
                user_email = payload.get("sub")
                user = db.query(User).filter(User.email == user_email).first()
        except:
            pass
    
    if not user:
         # Optional: Close if auth required, or continue as guest
         # await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
         # For now, we continue but might not save to specific user or save to default
         pass

    await live_handler.start_session(websocket, user, db)
