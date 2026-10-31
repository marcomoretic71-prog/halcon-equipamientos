import json, gzip, os
from io import BytesIO
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Restaura productos desde el ultimo backup de Google Drive (sin depender de BackupAutomatico DB)'

    def handle(self, *args, **options):
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        from google.auth.transport.requests import Request
        
        # Variables OAuth
        client_id = os.environ.get('GOOGLE_OAUTH_CLIENT_ID')
        client_secret = os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET')
        refresh_token = os.environ.get('GOOGLE_OAUTH_REFRESH_TOKEN')
        folder_id = os.environ.get('GOOGLE_DRIVE_FOLDER_ID')
        
        if not all([client_id, client_secret, refresh_token, folder_id]):
            self.stderr.write(self.style.ERROR("Faltan variables OAuth de Google"))
            return
        
        self.stdout.write("Conectando a Drive...")
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
        
        # Listar backups en Drive
        query = f"'{folder_id}' in parents and name contains 'backup_halcon' and trashed=false"
        results = service.files().list(q=query, orderBy='createdTime desc', pageSize=10, fields='files(id, name, createdTime, size)').execute()
        files = results.get('files', [])
        
        if not files:
            self.stderr.write(self.style.ERROR("No hay backups en Drive"))
            return
        
        self.stdout.write(f"Backups en Drive: {len(files)}")
        for f in files[:5]:
            self.stdout.write(f"  - {f['name']} | {f['createdTime']} | {f.get('size','')} bytes | ID: {f['id']}")
        
        ultimo = files[0]
        self.stdout.write("")
        self.stdout.write(f"Descargando ultimo backup: {ultimo['name']}...")
        
        # Descargar
        request = service.files().get_media(fileId=ultimo['id'])
        from googleapiclient.http import MediaIoBaseDownload
        fh = BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        
        fh.seek(0)
        # Descomprimir
        try:
            with gzip.GzipFile(fileobj=fh, mode='rb') as gz:
                data = json.loads(gz.read().decode('utf-8'))
        except:
            fh.seek(0)
            data = json.loads(fh.read().decode('utf-8'))
        
        productos_backup = data.get('productos', [])
        self.stdout.write(f"Productos en backup: {len(productos_backup)}")
        
        # Restaurar en DB
        from equipamientos.models import Producto
        from decimal import Decimal
        
        actuales = Producto.objects.count()
        self.stdout.write(f"Productos en DB actual: {actuales}")
        
        restaurados = 0
        for p_data in productos_backup:
            try:
                codigo = p_data.get('codigo')
                if not codigo:
                    continue
                try:
                    prod = Producto.objects.get(codigo=codigo)
                    continue
                except Producto.DoesNotExist:
                    Producto.objects.create(
                        codigo=codigo,
                        nombre=p_data.get('nombre',''),
                        precio=Decimal(str(p_data.get('precio',0))),
                        categoria=p_data.get('categoria',''),
                        stock=int(p_data.get('stock',0) or 0),
                    )
                    restaurados += 1
            except Exception as e:
                self.stderr.write(f"Error restaurando {p_data.get('codigo')}: {e}")
        
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"Restaurados {restaurados} productos borrados desde Drive"))
        self.stdout.write(f"Total ahora en DB: {Producto.objects.count()}")
