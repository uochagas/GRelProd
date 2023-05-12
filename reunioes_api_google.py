import yaml
import datetime
from pprint import pprint
from googleapiclient.discovery import build
from google.oauth2 import service_account
from google.auth.exceptions import RefreshError

def load_google_calendar_credentials():
    with open('config.yaml', 'r') as file:
        config = yaml.safe_load(file)
        credentials_file = config['GOOGLE_CALENDAR']['CREDENTIALS_FILE']
        calendar_id = config['GOOGLE_CALENDAR']['CALENDAR_ID']
        scopes = config['GOOGLE_CALENDAR']['SCOPES']
        api_name = config['GOOGLE_CALENDAR']['API_NAME']
        api_version = config['GOOGLE_CALENDAR']['API_VERSION']
    
    return credentials_file, calendar_id, scopes, api_name, api_version

def get_calendar_events(start_date, end_date):
    credentials_file, calendar_id, scopes, api_name, api_version = load_google_calendar_credentials()
    
    pprint(credentials_file)

    credentials = service_account.Credentials.from_service_account_file(
        credentials_file,
        scopes=scopes
        )
    
    # Criar o serviço de API do Google Agenda
    service = build(api_name, api_version, credentials=credentials)
    
    calendar_list = service.calendarList().list().execute()
    
    for calendar in calendar_list['items']:
        calendar_id = calendar['id']
        pprint(f'ID do Calendário: {calendar_id}')

    return []

def generate_calendar_report(start_date, end_date):
    events = get_calendar_events(start_date, end_date)

    pprint(f"Relatório de reuniões de {start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}:\n")
    if not events:
        pprint("Nenhuma reunião encontrada.")
    else:
        for event in events:
            event_title = event['summary']
            event_start = event['start'].get('dateTime', event['start'].get('date'))
            event_end = event['end'].get('dateTime', event['end'].get('date'))

            pprint(f"Título: {event_title}")
            pprint(f"Início: {event_start}")
            pprint(f"Término: {event_end}")
            pprint("--------------------")
