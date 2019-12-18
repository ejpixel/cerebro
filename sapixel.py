import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
import datetime

ONE_WEEK_IN_MINUTES = int(datetime.timedelta(days=7).total_seconds() / 60)
ONE_DAY_IN_MINUTES = int(datetime.timedelta(days=1).total_seconds() / 60)
TZ = "America/Sao_Paulo"
SCOPES = ['https://www.googleapis.com/auth/calendar']
SERVICE_ACCOUNT_FILE = os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
CALENDAR_ID = os.environ["CALENDAR_ID"]

models = {
    "accept_contract": {
        'summary': 'Assinar contrato',
        'description': 'Data limite para assinar o contrato',
        'start': {
            'dateTime': None,
            'timeZone': TZ,
        },
        'end': {
            'dateTime': None,
            'timeZone': TZ,
        },
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'popup', 'minutes': ONE_WEEK_IN_MINUTES},
                {'method': 'popup', 'minutes': ONE_DAY_IN_MINUTES}
            ],
        },
    },
    "first_payment": {
        'summary': 'Primeira parcela',
        'description': 'Data limite para o pagamento da primeira parcela',
        'start': {
            'dateTime': None,
            'timeZone': TZ,
        },
        'end': {
            'dateTime': None,
            'timeZone': TZ,
        },
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'popup', 'minutes': ONE_WEEK_IN_MINUTES},
                {'method': 'popup', 'minutes': ONE_DAY_IN_MINUTES}
            ],
        },
    },
    "payments": {
        'summary': 'Pagamento de parcela',
        'description': 'Data para o pagamento da parcela',
        'start': {
            'dateTime': None,
            'timeZone': TZ,
        },
        'end': {
            'dateTime': None,
            'timeZone': TZ,
        },
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'popup', 'minutes': ONE_WEEK_IN_MINUTES},
                {'method': 'popup', 'minutes': ONE_DAY_IN_MINUTES}
            ],
        },
    }
}


def new_calendar_event_from_model(model_name, start_date, end_date, title="", description=""):
    iso_start_date = str(datetime.datetime.isoformat(start_date.replace(microsecond=0), sep="T"))
    iso_end_date = str(datetime.datetime.isoformat(end_date.replace(microsecond=0), sep="T"))
    event = models[model_name]
    event["start"]["dateTime"] = iso_start_date
    event["end"]["dateTime"] = iso_end_date
    event["summary"] += title
    event["description"] += description
    create_calendar_event(event)


def create_calendar_event(event):
    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)

    service = build('calendar', 'v3', credentials=credentials)

    service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
