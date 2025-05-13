from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os
import pickle
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/calendar']

class GoogleCalendarService:
    def __init__(self):
        self.creds = None
        self.service = None
        self.calendar_id = 'primary'  # Use primary calendar by default

    def authenticate(self) -> bool:
        """Authenticate with Google Calendar API."""
        try:
            if os.path.exists('token.pickle'):
                with open('token.pickle', 'rb') as token:
                    self.creds = pickle.load(token)

            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        'credentials.json', SCOPES)
                    self.creds = flow.run_local_server(port=0)

                with open('token.pickle', 'wb') as token:
                    pickle.dump(self.creds, token)

            self.service = build('calendar', 'v3', credentials=self.creds)
            return True

        except Exception as e:
            logger.error(f"Error authenticating with Google Calendar: {str(e)}")
            return False

    def get_events(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Get events from Google Calendar for the specified date range."""
        try:
            if not self.service and not self.authenticate():
                return []

            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=start_date.isoformat() + 'Z',
                timeMax=end_date.isoformat() + 'Z',
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            events = events_result.get('items', [])
            formatted_events = []

            for event in events:
                try:
                    start = event['start'].get('dateTime', event['start'].get('date'))
                    end = event['end'].get('dateTime', event['end'].get('date'))

                    formatted_event = {
                        'external_id': event['id'],
                        'summary': event.get('summary', ''),
                        'description': event.get('description', ''),
                        'start_time': datetime.fromisoformat(start.replace('Z', '+00:00')),
                        'end_time': datetime.fromisoformat(end.replace('Z', '+00:00')),
                        'status': event.get('status', 'confirmed'),
                        'attendees': [attendee['email'] for attendee in event.get('attendees', [])],
                        'location': event.get('location', ''),
                    }
                    formatted_events.append(formatted_event)

                except Exception as e:
                    logger.error(f"Error formatting event: {str(e)}")
                    continue

            return formatted_events

        except Exception as e:
            logger.error(f"Error getting events from Google Calendar: {str(e)}")
            return []

    def create_event(self, event_data: Dict) -> Optional[str]:
        """Create a new event in Google Calendar."""
        try:
            if not self.service and not self.authenticate():
                return None

            event = {
                'summary': event_data.get('summary', 'Appointment'),
                'description': event_data.get('description', ''),
                'start': {
                    'dateTime': event_data['start_time'].isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': event_data['end_time'].isoformat(),
                    'timeZone': 'UTC',
                },
                'attendees': [{'email': email} for email in event_data.get('attendees', [])],
                'location': event_data.get('location', ''),
            }

            event = self.service.events().insert(
                calendarId=self.calendar_id,
                body=event
            ).execute()

            return event['id']

        except Exception as e:
            logger.error(f"Error creating event in Google Calendar: {str(e)}")
            return None

    def update_event(self, event_id: str, event_data: Dict) -> bool:
        """Update an existing event in Google Calendar."""
        try:
            if not self.service and not self.authenticate():
                return False

            event = {
                'summary': event_data.get('summary', 'Appointment'),
                'description': event_data.get('description', ''),
                'start': {
                    'dateTime': event_data['start_time'].isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': event_data['end_time'].isoformat(),
                    'timeZone': 'UTC',
                },
                'attendees': [{'email': email} for email in event_data.get('attendees', [])],
                'location': event_data.get('location', ''),
            }

            self.service.events().update(
                calendarId=self.calendar_id,
                eventId=event_id,
                body=event
            ).execute()

            return True

        except Exception as e:
            logger.error(f"Error updating event in Google Calendar: {str(e)}")
            return False

    def delete_event(self, event_id: str) -> bool:
        """Delete an event from Google Calendar."""
        try:
            if not self.service and not self.authenticate():
                return False

            self.service.events().delete(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()

            return True

        except Exception as e:
            logger.error(f"Error deleting event from Google Calendar: {str(e)}")
            return False 