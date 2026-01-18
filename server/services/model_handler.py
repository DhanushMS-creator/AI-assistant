import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

from .calendar_handler import calendar_handler

class ModelHandler:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_CLOUD_API_KEY")
        self.client = genai.Client(
            vertexai=True,
            api_key=self.api_key
        )
        self.model_name = "gemini-2.0-flash-exp"
        
        # Define Tools
        # NOTE: In a real app, 'user' object must be passed to tools. 
        # Since 'generate_response' doesn't have 'user' yet, we need to update it.
        # For now, we define the tool definitions. Actual execution logic needs to handle context.
        
        self.tools = [
            types.Tool(google_search=types.GoogleSearch()),
            # We define functions that the model can call. 
            # Ideally, we should register the python functions directly if using the high-level SDK 
            # that supports automatic execution.
            # But here we are using `genai.Client` manually.
            # For simplicity, we will instruct the model about tools in the system prompt for now
            # OR register them if the SDK supports `function_declarations`.
            
            # Let's try to register the python functions directly as tools:
            types.Tool(function_declarations=[
                types.FunctionDeclaration(
                    name="get_calendar_events",
                    description="Get upcoming events from the user's Google Calendar.",
                ),
                types.FunctionDeclaration(
                    name="schedule_event",
                    description="Schedule a new event on Google Calendar.",
                    parameters=types.Schema(
                        type="OBJECT",
                        properties={
                            "summary": types.Schema(type="STRING", description="Title of the event"),
                            "start_time": types.Schema(type="STRING", description="Start time in ISO format (e.g. 2024-01-01T10:00:00)"),
                        },
                        required=["summary", "start_time"]
                    )
                )
            ])
        ]
        
        self.config = types.GenerateContentConfig(
            temperature=0.7, # Lower temp for tool use
            top_p=0.95,
            max_output_tokens=8192,
            tools=self.tools,
            system_instruction=types.Content(
                parts=[types.Part(
                    text="You are Nova, a personal AI voice assistant with access to Google Calendar. "
                         "Capabilities: "
                         "1. You can search the web for real-time info. "
                         "2. You can check the user's calendar and schedule events. "
                         "3. If asked to schedule, ALWAYS ask for confirmation of time before calling the tool if ambiguous. "
                         "4. Be concise and friendly. Spoken conversation style."
                )]
            ),
        )

        self.history = []

    # Updated signature to accept 'user' object
    async def generate_response(self, user_input: str, user=None) -> str:
        try:
            # Personalization Context
            import datetime
            now = datetime.datetime.now().strftime("%A, %d %B %Y, %I:%M %p")
            user_name = user.name if user else "User"
            
            # Create a dynamic prompt with user context
            # We copy the base tools but update the system instruction
            dynamic_instruction = (
                f"You are Nova, a personal AI voice assistant for {user_name}. "
                f"The current time is {now}. "
                "Capabilities: "
                "1. You can search the web for real-time info. "
                "2. You can check the user's calendar and schedule events. "
                "3. If asked to schedule, ALWAYS ask for confirmation of time before calling the tool if ambiguous. "
                "4. Be concise and friendly. Spoken conversation style."
            )

            # Construct content with history
            contents = []
            for msg in self.history:
                contents.append(types.Content(role=msg["role"], parts=[types.Part(text=msg["text"])]))
            
            contents.append(types.Content(role="user", parts=[types.Part(text=user_input)]))
            
            # Temporary config override for this request
            request_config = types.GenerateContentConfig(
                temperature=0.7,
                top_p=0.95,
                max_output_tokens=8192,
                tools=self.tools,
                system_instruction=types.Content(
                    parts=[types.Part(text=dynamic_instruction)]
                ),
            )
            
            # 1. Generate content
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=request_config
            )
            
            final_text = ""

            # 2. Check for Function Calls
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if part.function_call:
                        fn = part.function_call
                        print(f"Function Call Detected: {fn.name}")
                        
                        tool_result = "Tool execution failed."
                        
                        if user:
                            if fn.name == "get_calendar_events":
                                tool_result = calendar_handler.list_events(user)
                            elif fn.name == "schedule_event":
                                args = fn.args
                                tool_result = calendar_handler.create_event(user, args.get('summary'), args.get('start_time'))
                        else:
                            tool_result = "Error: User context missing for calendar operation."

                        print(f"Tool Result: {tool_result}")

                        # 3. Send Tool Output back to model to get final spoken response
                        # We need to construct the function response part
                        
                        # Add the model's function call to history (ephemeral for this turn)
                        contents.append(response.candidates[0].content)
                        
                        # Add the function response
                        contents.append(types.Content(
                            parts=[types.Part(
                                function_response=types.FunctionResponse(
                                    name=fn.name,
                                    response={"result": tool_result}
                                )
                            )]
                        ))
                        
                        # Generate final response
                        final_res = self.client.models.generate_content(
                            model=self.model_name,
                            contents=contents,
                            config=request_config
                        )
                        
                        if final_res.text:
                            final_text = final_res.text
                    
                    elif part.text:
                        final_text += part.text
            
            if not final_text:
                final_text = "I'm not sure how to handle that."

            # Update history
            self.history.append({"role": "user", "text": user_input})
            self.history.append({"role": "model", "text": final_text})
            
            return final_text

        except Exception as e:
            print(f"Error generating response: {e}")
            return f"Error: {str(e)}"

model_handler = ModelHandler()
