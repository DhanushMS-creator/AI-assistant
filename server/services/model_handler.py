import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

class ModelHandler:
    def __init__(self):
        # Using GEMINI_API_KEY from .env but mapped to api_key argument
        # The user snippet used vertexai=True, we will keep it but it might need project/location if not implicit.
        # If vertexai=True fails with just API key, we might need to set it to False or ensure env vars are right.
        # For 'gemini-3-pro-preview', it usually requires Vertex AI or the specific preview API.
        # Let's try with http_options or just api_key as requested.
        
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_CLOUD_API_KEY")
        self.client = genai.Client(
            vertexai=True,
            api_key=self.api_key
        )
        self.model_name = "gemini-2.0-flash-exp"
        
        # Tools and Config configuration
        self.tools = [
            types.Tool(google_search=types.GoogleSearch()),
        ]
        
        self.config = types.GenerateContentConfig(
            temperature=1,
            top_p=0.95,
            max_output_tokens=8192,
            safety_settings=[
                types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="OFF"),
                types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="OFF"),
                types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="OFF"),
                types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="OFF")
            ],
            tools=self.tools,
            thinking_config=types.ThinkingConfig(
                thinking_level="HIGH",
            ),
            system_instruction=types.Content(
                parts=[types.Part(
                    text="You are a personal voice assistant. Your response will be spoken out loud. "
                         "1. Respond in a friendly, natural, and conversational manner. "
                         "2. DO NOT use any special characters or formatting like asterisks (**), hashes (#), or bullets (-). "
                         "3. formatting like bold or italics is strictly forbidden as it cannot be spoken. "
                         "4. Keep answers concise and direct. "
                         "5. If you need to list things, just speak them naturally in a sentence."
                )]
            ),
        )

        # Basic history management (simplified for this demo)
        self.history = []

    async def generate_response(self, user_input: str) -> str:
        try:
            # Construct content with history
            contents = []
            for msg in self.history:
                contents.append(types.Content(role=msg["role"], parts=[types.Part(text=msg["text"])]))
            
            # Add current user message
            contents.append(types.Content(role="user", parts=[types.Part(text=user_input)]))

            # Generate via streaming but accumulate for return
            full_response = ""
            # Note: client.models.generate_content_stream is synchronous in the snippet? 
            # The SDK might have an async version or we run it in a thread if it blocks too much.
            # Checking SDK docs: usually has async_generate_content. 
            # But the user snippet used: for chunk in client.models.generate_content_stream...
            # We will try to use the synchronous stream for now, wrapped or just directly if fast enough.
            # Ideally we should use `await client.aio.models.generate_content_stream` if available for async.
            # Assuming standard usage first.
            
            # Use 'aio' client if available for async, or just standard client.
            # The new SDK has an .aio accessor? Or we use `genai.Client` vs `genai.AsyncClient`?
            # The snippet used `genai.Client`. Let's stick to valid async if possible or blocking for now.
            # Actually, let's wrap it for safety or checking if `generate_content` is enough.
            
            # Let's just use the snippet pattern but accumulate.
            
            response_stream = self.client.models.generate_content_stream(
                model=self.model_name,
                contents=contents,
                config=self.config
            )

            for chunk in response_stream:
                if chunk.candidates and chunk.candidates[0].content and chunk.candidates[0].content.parts:
                     # Check if it's text
                    for part in chunk.candidates[0].content.parts:
                        if part.text:
                            full_response += part.text

            # Update history
            self.history.append({"role": "user", "text": user_input})
            self.history.append({"role": "model", "text": full_response})
            
            return full_response

        except Exception as e:
            print(f"Error generating response: {e}")
            return f"Error: {str(e)}"

model_handler = ModelHandler()
