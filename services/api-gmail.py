from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# Cambié el alcance para permitir eliminar mensajes permanentemente
SCOPES = ["https://mail.google.com/"]

def main():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    
    # Si las credenciales son inválidas o han caducado, re-autenticar
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        
        # Guardar las credenciales para la próxima ejecución
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        # Construir el servicio y llamar a la API de Gmail
        service = build("gmail", "v1", credentials=creds)
        results = service.users().messages().list(
            userId="me", maxResults=2, q="category:promotions"
        ).execute()
        messages = results.get("messages", [])

        if not messages:
            print("No messages found in Promotions.")
            return

        print("Deleting the first 2 messages in Promotions:")
        for message in messages:
            service.users().messages().delete(userId="me", id=message["id"]).execute()
            print(f"Deleted message ID: {message['id']}")

    except HttpError as error:
        print(f"An error occurred: {error}")

if __name__ == "__main__":
    main()

