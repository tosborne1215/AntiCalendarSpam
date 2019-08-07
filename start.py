from datetime import timedelta, datetime
import pickle
import os.path
import re
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/calendar']


def main():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    calender_service = build('calendar', 'v3', credentials=creds)
    gmail_service = build('gmail', 'v1', credentials=creds)

    events = get_events(calender_service)
    spam_emails = get_spam_emails(gmail_service)
    bad_results = cross_reference(events, spam_emails)
    print(spam_emails)
    print(bad_results)
    delete_events(calender_service, bad_results)


def get_events(service):
    email_event_map = dict()
    # Call the Calendar API
    now = datetime.utcnow() - timedelta(days=1)
    events_result = service.events().list(calendarId='primary', timeMin=now.isoformat() + 'Z',
                                          maxResults=10, singleEvents=True,
                                          orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        print('No upcoming events found.')
    for event in events:
        if event['creator']['email'] is not '':
            if event['creator']['email'] not in email_event_map.keys():
                email_event_map[event['creator']['email']] = []
            email_event_map[event['creator']['email']].append(event['id'])

    return email_event_map


def get_spam_emails(service):
    emails = dict()
    # Call the Gmail API
    results = service.users().messages().list(userId='me', maxResults=25, labelIds='SPAM', includeSpamTrash=True).execute()
    messages = results.get('messages', [])

    if not messages:
        print('No messages found.')
    else:
        for message in messages:
            individual_result = service.users().messages().get(userId='me', id=message['id'], format='metadata').execute()
            email = extract_from_email(individual_result)
            emails[email] = 0

    return emails.keys()


def extract_from_email(message):
    for header in message['payload']['headers']:
        if header['name'] == 'From':
            return extract_email_from_header(header['value'])


def extract_email_from_header(header_value):
    regex = re.compile(r'[^@<\s]+@[^@\s>]+')
    return regex.findall(header_value)[-1]


def cross_reference(events_dict, emails_list):
    bad_results = []
    for email in emails_list:
        if email in events_dict.keys():
            bad_results.extend(events_dict[email])
    return bad_results


def delete_events(service, events, dry=False):
    # TODO: https://github.com/googleapis/google-api-python-client/blob/83ead9be84f7e697f8140a77d85eb0ce2eee3538/docs/batch.md
    batch = service.new_batch_http_request()
    for event in events:
        print("deleting eventId " + event)
        if not dry:
            print("for real")
            batch.add(service.events().delete(calendarId='primary', eventId=event, sendNotifications=False, sendUpdates='all'))
    batch.execute()


if __name__ == '__main__':
    main()
