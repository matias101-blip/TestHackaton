import json
from django.http import JsonResponse
from django.shortcuts import render
from django.views import View
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

SCOPES = ["https://mail.google.com/"]

class NameView(View):
    template_name = 'prueba/prueba.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        filter_messages = data.get('filter_messages')
        print(f"Filter messages: {filter_messages}")
        
        creds = None
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "credentials.json", SCOPES
                )
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
                return JsonResponse({'message': 'No messages found in Promotions.'})
            
            message_contents = []
            for message in messages:
                msg = service.users().messages().get(userId="me", id=message['id']).execute()
                msg_snippet = msg.get('snippet')
                message_contents.append(msg_snippet)
            
            context = {
                'message_contents': message_contents
            }
            
            # for message in message_contents:
            #     print(f"Message: {message}")
                
            
            return JsonResponse(context)
        
        except HttpError as error:
            return JsonResponse({'error': str(error)})
