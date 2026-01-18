from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import datetime
import json
import os

class CalendarHandler:
    def __init__(self):
        self.client_id = os.getenv("GOOGLE_CLIENT_ID")
        self.client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        self.token_uri = "https://oauth2.googleapis.com/token"

    def get_service(self, user):
        """Builds the Calendar service using the user's refresh token."""
        if not user.refresh_token:
            print(f"No refresh token for user {user.email}")
            return None

        # Reconstruct Credentials object
        creds = Credentials(
            token=None, # Access token will be refreshed
            refresh_token=user.refresh_token,
            token_uri=self.token_uri,
            client_id=self.client_id,
            client_secret=self.client_secret
        )

        return build('calendar', 'v3', credentials=creds)

    def list_events(self, user):
        try:
            service = self.get_service(user)
            if not service:
                return "I don't have permission to access your calendar. Please login again and grant permissions."

            now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
            print(f"Getting events via refresh token for user: {user.email}")
            
            events_result = service.events().list(
                calendarId='primary', 
                timeMin=now,
                maxResults=10, 
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])

            if not events:
                return "No upcoming events found."

            event_list = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                event_list.append(f"- {event['summary']} at {start}")
            
            return "\n".join(event_list)

        except Exception as e:
            print(f"Calendar List Error: {e}")
            return "Failed to retrieve calendar events."

    def create_event(self, user, summary, start_time_str, duration_minutes=60):
        try:
            service = self.get_service(user)
            if not service:
                return "Auth Error: No access to calendar."

            # Simple parsing for demo purposes - expects ISO format or close to it
            # In a real app, AI should output standardized ISO strings
            # But let's assume Gemini gives us something usable or we default to 'tomorrow'
            
            try:
                # Try parsing basic ISO
                start_dt = datetime.datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))
            except:
                # Fallback: Create for "Tomorrow 9am" if parsing fails, just for safety
                start_dt = datetime.datetime.now() + datetime.timedelta(days=1)
                start_dt = start_dt.replace(hour=9, minute=0, second=0, microsecond=0)
                print(f"Could not parse '{start_time_str}', defaulting to tomorrow 9am")

            end_dt = start_dt + datetime.timedelta(minutes=duration_minutes)

            event = {
                'summary': summary,
                'start': {
                    'dateTime': start_dt.isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': end_dt.isoformat(),
                    'timeZone': 'UTC',
                },
            }

            event = service.events().insert(calendarId='primary', body=event).execute()
            return f"Event created: {event.get('htmlLink')}"

        except Exception as e:
            print(f"Calendar Create Error: {e}")
            return f"Failed to create event: {e}"

calendar_handler = CalendarHandler()
