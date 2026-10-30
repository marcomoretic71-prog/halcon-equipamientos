import os
import json
import gzip
import base64
from io import BytesIO
from django.core.management.base import BaseCommand
from django.utils import timezone

class Command(BaseCommand):
    help = 'Backup HALCON + subida a Drive via OAuth (cuenta personal)'

    def add_arguments(self, parser):
        parser.add_argument('--tipo', default='MANUAL', choices=['AUTO','VENTA','MANUAL','PRECIO'])

    def handle(self, *args, **options):
        from equipamientos.models import (
            Cliente, Producto, Presupuesto, ItemPresupuesto,
            ListaPrecio, ItemListaPrecio, Venta, ItemVenta,
            MovimientoCaja, BackupAutomatico
        )
        tipo = options['tipo']
        ahora = timezone.now()
        ts = ahora.strftime('%Y%m%d_%H%M%S')

        data = {}
        try:
            data['clientes'] = list(Cliente.objects.values())
            data['productos'] = list(Producto.objects.values())
            data['presupuestos'] = list(Presupuesto.objects.values())
            data['items_presupuesto'] = list(ItemPresupuesto.objects.values())
            data['listas_precio'] = list(ListaPrecio.objects.values())
            data['items_lista_precio'] = list(ItemListaPrecio.objects.values())
            data['ventas'] = list(Venta.objects.values())
            data['items_venta'] = list(ItemVenta.objects.values())
            data['movimientos_caja'] = list(MovimientoCaja.objects.values())
            try:
                from equipamientos.models import ProductoHistorial
                data['historial_precios'] = list(ProductoHistorial.objects.values().order_by('-fecha')[:1000])
            except:
                pass
        except Exception as e:
            self.stderr.write(f"Error recolectando: {e}")
            data['error'] = str(e)

        n_productos = len(data.get('productos', []))
        n_ventas = len(data.get('ventas', []))
        n_clientes = len(data.get('clientes', []))

        json_str = json.dumps(data, default=str, ensure_ascii=False, indent=2)
        json_bytes = json_str.encode('utf-8')
        gz_buffer = BytesIO()
        with gzip.GzipFile(fileobj=gz_buffer, mode='wb') as gz:
            gz.write(json_bytes)
        gz_bytes = gz_buffer.getvalue()
        tam_kb = len(gz_bytes) / 1024
        nombre = f"backup_halcon_{ts}_{tipo}.json.gz"

        try:
            BackupAutomatico.objects.create(
                tipo=tipo,
                archivo_nombre=nombre,
                archivo_json=gz_bytes,
                cantidad_productos=n_productos,
                cantidad_clientes=n_clientes,
                cantidad_ventas=n_ventas,
                tamano_kb=round(tam_kb,2)
            )
            self.stdout.write(self.style.SUCCESS(f"Backup DB OK: {nombre} - {tam_kb:.1f}KB Prod:{n_productos}"))
        except Exception as e:
            self.stderr.write(f"Error DB: {e}")

        tmp_path = f"/tmp/{nombre}"
        try:
            with open(tmp_path, 'wb') as f:
                f.write(gz_bytes)
        except:
            tmp_path = os.path.join(os.getcwd(), nombre)
            with open(tmp_path, 'wb') as f:
                f.write(gz_bytes)

        ok = self.subir_a_drive_oauth(tmp_path, nombre)
        if ok:
            self.stdout.write(self.style.SUCCESS("✅ Subido a Drive con OAuth"))
        else:
            self.stdout.write(self.style.WARNING("⚠️ No se subió a Drive - revisa variables OAuth"))

    def subir_a_drive_oauth(self, file_path, file_name):
        folder_id = os.environ.get('GOOGLE_DRIVE_FOLDER_ID')
        client_id = os.environ.get('GOOGLE_OAUTH_CLIENT_ID')
        client_secret = os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET')
        refresh_token = os.environ.get('GOOGLE_OAUTH_REFRESH_TOKEN')

        if not folder_id or not client_id or not client_secret or not refresh_token:
            print("Faltan variables OAuth: GOOGLE_DRIVE_FOLDER_ID, CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN")
            return False
        try:
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build
            from googleapiclient.http import MediaFileUpload
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

            media = MediaFileUpload(file_path, mimetype='application/gzip', resumable=True)
            metadata = {'name': file_name, 'parents': [folder_id]}
            file = service.files().create(body=metadata, media_body=media, fields='id').execute()
            print(f"Drive ID: {file.get('id')}")
            return True
        except Exception as e:
            print(f"Error Drive OAuth: {e}")
            import traceback; traceback.print_exc()
            return False
