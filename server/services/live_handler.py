import os
import asyncio
from google import genai
from google.genai import types
from dotenv import load_dotenv
from ..models import Session as ChatSession, Message
from datetime import datetime
from pathlib import Path

# Load .env from server directory
# Load .env from project root directory
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

class LiveHandler:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
             print("Warning: GEMINI_API_KEY not found in env")
             
        self.client = genai.Client(
            vertexai=False,
            api_key=self.api_key,
            http_options={"api_version": "v1alpha"}
        )
        self.model_name = "gemini-2.0-flash-exp"
        self.config = {"response_modalities": ["AUDIO"]}

    async def start_session(self, websocket, user=None, db=None):
        """
        Manages the bidirectional bridge between the Client WebSocket and Gemini Live Session.
        """
        try:
            chat_session_id = None
            if db and user:
                # Create DB Session
                new_session = ChatSession(user_id=user.id, title=f"Live Session {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}")
                db.add(new_session)
                db.commit()
                db.refresh(new_session)
                chat_session_id = new_session.id
                print(f"Started DB Session: {chat_session_id}")

            # Basic config for Audio-only output
            async with self.client.aio.live.connect(model=self.model_name, config=self.config) as session:
                print("Connected to Gemini Live")
                
                client_task = asyncio.create_task(self.receive_from_client(websocket, session))
                model_task = asyncio.create_task(self.send_to_client(websocket, session))
                
                await asyncio.wait(
                    [client_task, model_task],
                    return_when=asyncio.FIRST_COMPLETED,
                )
                    
        except Exception as e:
            print(f"Live Session Error: {e}")
            try:
                await websocket.send_text(f"Error: {str(e)}")
            except:
                pass
            await websocket.close()

    async def receive_from_client(self, websocket, session):
        try:
            while True:
                # Receive audio chunk from client (bytes) or text (json)
                message = await websocket.receive()
                
                if "bytes" in message:
                    audio_data = message["bytes"]
                    # Send audio to Gemini (audio/pcm is preferred for raw)
                    await session.send(input={"data": audio_data, "mime_type": "audio/pcm"}, end_of_turn=False)
                elif "text" in message:
                     pass
                     
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"Error receiving from client: {e}")

    async def send_to_client(self, websocket, session):
        try:
            while True:
                async for response in session.receive():
                    # Gemini sends back audio chunks, we forward to client
                    if response.data:
                        # Send binary audio back
                        await websocket.send_bytes(response.data)
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"Error sending to client: {e}")

live_handler = LiveHandler()
