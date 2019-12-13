import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
import datetime

def create_calendar_event(start_date, end_date):
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    CALENDAR_ID = os.getenv("CALENDAR_ID")


    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)

    service = build('calendar', 'v3', credentials=credentials)

    tz = "America/Sao_Paulo"

    event = {
        'summary': 'Primeiro pagamento',
        'description': 'Data limite para pagamento da primeira parcela',
        'start': {
            'dateTime': start_date,
            'timeZone': tz,
        },
        'end': {
            'dateTime': end_date,
            'timeZone': tz,
        },
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'popup', 'minutes': 3 * 24 * 60},
            ],
        },
    }

    event = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
