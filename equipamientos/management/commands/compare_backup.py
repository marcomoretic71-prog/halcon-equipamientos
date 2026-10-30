from django.core.management.base import BaseCommand
import os, json, gzip, base64
from io import BytesIO
from datetime import datetime

class Command(BaseCommand):
    help = 'Compara backup de Drive con DB actual para encontrar precios que cambiaron a las 11:45'

    def add_arguments(self, parser):
        parser.add_argument('--drive-id', type=str, help='ID de archivo de Drive a comparar')

    def handle(self, *args, **options):
        from equipamientos.models import Producto
        drive_id = options['drive_id']
        if not drive_id:
            self.stderr.write("Pasame --drive-id ID_del_archivo")
            return

        folder_id = os.environ.get('GOOGLE_DRIVE_FOLDER_ID')
        client_id = os.environ.get('GOOGLE_OAUTH_CLIENT_ID')
        client_secret = os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET')
        refresh_token = os.environ.get('GOOGLE_OAUTH_REFRESH_TOKEN')

        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        from google.auth.transport.requests import Request
        import io
        from googleapiclient.http import MediaIoBaseDownload

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

        # Descargar archivo
        request = service.files().get_media(fileId=drive_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        gz_bytes = fh.getvalue()
        
        self.stdout.write(f"Descargado {len(gz_bytes)} bytes")

        # Descomprimir
        try:
            with gzip.GzipFile(fileobj=BytesIO(gz_bytes), mode='rb') as gz:
                data = json.loads(gz.read().decode('utf-8'))
        except Exception as e:
            self.stderr.write(f"Error descomprimiendo: {e}")
            return

        backup_prods = {p['codigo']: p for p in data.get('productos', [])}
        self.stdout.write(f"Productos en backup {drive_id}: {len(backup_prods)}")

        actuales = {p.codigo: p for p in Producto.objects.all()}
        self.stdout.write(f"Productos en DB actual: {len(actuales)}")

        diffs = []
        for cod, p_backup in backup_prods.items():
            p_act = actuales.get(cod)
            if not p_act:
                diffs.append((cod, 'BORRADO', p_backup.get('precio'), None, p_backup.get('stock'), None))
            else:
                precio_b = str(p_backup.get('precio',''))
                precio_a = str(getattr(p_act, 'precio', ''))
                stock_b = str(p_backup.get('stock','') or p_backup.get('cantidad',''))
                stock_a = str(getattr(p_act, 'stock', getattr(p_act, 'cantidad', '')))
                if precio_b != precio_a or stock_b != stock_a:
                    diffs.append((cod, p_backup.get('nombre','')[:30], precio_b, precio_a, stock_b, stock_a))

        self.stdout.write(f"Diferencias encontradas: {len(diffs)}")
        for cod, nombre, pb, pa, sb, sa in diffs[:100]:
            self.stdout.write(f"  {cod} | {nombre} | Precio backup:{pb} -> actual:{pa} | Stock backup:{sb} -> actual:{sa}")
        
        if len(diffs) == 0:
            self.stdout.write(self.style.SUCCESS("No hay diferencias de precio/stock entre ese backup y la DB actual"))
