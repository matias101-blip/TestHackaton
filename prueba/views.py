import json
from django.http import JsonResponse
from django.views import View
from django.shortcuts import render
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

SCOPES = ["https://mail.google.com/"]

class NameView(View):
    def get(self, request, *args, **kwargs):
        # Renderizar la plantilla cuando se accede con GET
        return render(request, 'prueba/prueba.html')

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        filter_messages = data.get('filter_messages')
        
        creds = None
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
                creds = flow.run_local_server(port=0)
            with open("token.json", "w") as token:
                token.write(creds.to_json())

        try:
            service = build("gmail", "v1", credentials=creds)
            results = service.users().messages().list(
                userId="me", maxResults=2, q=f"category:{filter_messages}"
            ).execute()
            messages = results.get("messages", [])

            if not messages:
                return JsonResponse({'message': 'No messages found.'})
            
            message_contents = []
            for message in messages:
                msg = service.users().messages().get(userId="me", id=message['id']).execute()
                
                headers = msg.get("payload", {}).get("headers", [])
                sender = next((header["value"] for header in headers if header["name"] == "From"), "Remitente desconocido")
                subject = next((header["value"] for header in headers if header["name"] == "Subject"), "Sin asunto")
                
                profile_image_url = f"https://www.gravatar.com/avatar/{hash(sender)}?d=identicon"

                message_contents.append({
                    'id': message['id'],
                    'sender': sender,
                    'subject': subject,
                    'profileImage': profile_image_url,
                })
            
            return JsonResponse({'message_contents': message_contents})
        
        except HttpError as error:
            return JsonResponse({'error': str(error)})

class DeleteEmailsView(View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        message_ids = data.get('message_ids', [])

        if not message_ids:
            return JsonResponse({'error': 'No emails selected for deletion.'}, status=400)

        try:
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)
            service = build("gmail", "v1", credentials=creds)

            for msg_id in message_ids:
                service.users().messages().delete(userId="me", id=msg_id).execute()

            return JsonResponse({'success': True})

        except HttpError as error:
            return JsonResponse({'error': f'Error deleting emails: {error}'}, status=500)
