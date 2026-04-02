import os.path
import pickle
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from libs.core.logger import configure_logger

logger = configure_logger("gmail_client")

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

class GmailClient:
    def __init__(self):
        self.creds = None
        self.service = None
        self._authenticate()

    def _authenticate(self):
        """Shows basic usage of the Gmail API.
        Lists the user's Gmail labels.
        """
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                self.creds = pickle.load(token)
        
        # If there are no (valid) credentials available, let the user log in.
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                # Note: This flow requires a browser, which might be tricky in headless docker.
                # For production, we should mount the token.pickle or use a service account (if applicable for Workspace)
                # or generate the token locally and mount it.
                if os.path.exists('credentials.json'):
                    flow = InstalledAppFlow.from_client_secrets_file(
                        'credentials.json', SCOPES)
                    self.creds = flow.run_local_server(port=0)
                else:
                    logger.error("credentials.json not found.")
                    return

            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(self.creds, token)

        self.service = build('gmail', 'v1', credentials=self.creds)
        logger.info("Gmail API service built successfully.")

    def list_messages(self, query="is:unread"):
        """
        List all messages matching the query.
        """
        if not self.service:
            logger.error("Gmail service not initialized.")
            return []

        try:
            results = self.service.users().messages().list(userId='me', q=query).execute()
            messages = results.get('messages', [])
            logger.info(f"Found {len(messages)} messages.")
            return messages
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            return []

    def get_message(self, msg_id):
        """
        Get a specific message by ID.
        """
        if not self.service:
            return None
        try:
            message = self.service.users().messages().get(userId='me', id=msg_id).execute()
            return message
        except Exception as e:
            logger.error(f"An error occurred fetching message {msg_id}: {e}")
            return None
