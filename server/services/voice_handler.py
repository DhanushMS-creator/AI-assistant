import os
from google.cloud import speech
from google.cloud import texttospeech
from dotenv import load_dotenv

load_dotenv()

# We assume credentials are set via GOOGLE_APPLICATION_CREDENTIALS env var
# or default gcloud auth application-default login

class VoiceHandler:
    def __init__(self):
        try:
            self.speech_client = speech.SpeechClient()
            self.tts_client = texttospeech.TextToSpeechClient()
        except Exception as e:
            print(f"Voice clients failed to initialize: {e}")
            self.speech_client = None
            self.tts_client = None

    async def speech_to_text(self, audio_content: bytes) -> str:
        audio = speech.RecognitionAudio(content=audio_content)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS, # Browser standard
            sample_rate_hertz=48000,
            language_code="en-US",
        )

        if not self.speech_client:
            return ""
        try:
            response = self.speech_client.recognize(config=config, audio=audio)
            
            # Just get the first result
            if response.results:
                return response.results[0].alternatives[0].transcript
            return ""
        except Exception as e:
            print(f"STT Error: {e}")
            return ""

    async def text_to_speech(self, text: str) -> bytes:
        synthesis_input = texttospeech.SynthesisInput(text=text)

        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
        )

        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )

        if not self.tts_client:
            return None

        try:
            response = self.tts_client.synthesize_speech(
                input=synthesis_input, voice=voice, audio_config=audio_config
            )
            return response.audio_content
        except Exception as e:
            print(f"TTS Error: {e}")
            return None

voice_handler = VoiceHandler()
