from django.core.management.base import BaseCommand
import os

class Command(BaseCommand):
    help = 'Lista todos los backups en Drive HALCON_BACKUPS'

    def handle(self, *args, **options):
        folder_id = os.environ.get('GOOGLE_DRIVE_FOLDER_ID')
        client_id = os.environ.get('GOOGLE_OAUTH_CLIENT_ID')
        client_secret = os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET')
        refresh_token = os.environ.get('GOOGLE_OAUTH_REFRESH_TOKEN')

        if not folder_id:
            self.stderr.write("Falta GOOGLE_DRIVE_FOLDER_ID")
            return

        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        from google.auth.transport.requests import Request

        creds = Credentials(
            None,
            refresh_token=refresh_token,
            token_uri='https://oauth2.googleapis.com/token',
            client_id=client_id,
            client_secret=client_secret,
            scopes=['https://www.googleapis.com/auth/drive']
        )
        creds.refresh(Request())
        service = build('drive', 'v3', credentials=creds)

        # Listar archivos en la carpeta
        results = service.files().list(
            q=f"'{folder_id}' in parents and trashed=false",
            fields="files(id, name, size, createdTime, modifiedTime)",
            orderBy="createdTime desc",
            pageSize=100
        ).execute()
        files = results.get('files', [])
        
        self.stdout.write(f"Backups en Drive HALCON_BACKUPS: {len(files)}")
        for f in files:
            size_kb = int(f.get('size',0))/1024 if f.get('size') else 0
            self.stdout.write(f"  {f['createdTime'][:19]} | {f['name']} | {size_kb:.1f}KB | ID: {f['id']}")

        # Si quiere comparar 2 backups
        self.stdout.write("")
        self.stdout.write("Para comparar un backup de ayer con el de hoy y ver que cambio a las 11:45, decime 2 IDs y corro diff")
