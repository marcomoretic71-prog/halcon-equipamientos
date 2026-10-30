import json, os, gzip, base64
from datetime import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from equipamientos.models import Producto, Venta, ItemVenta, Cliente, MovimientoCaja, Presupuesto, ItemPresupuesto

def upload_to_drive(file_path, file_name):
    """Sube archivo a Google Drive si hay credenciales, si no, no falla"""
    try:
        # Buscar credenciales en env vars
        folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID')
        creds_json_b64 = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON_B64')
        creds_json_raw = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
        
        if not folder_id:
            print("No hay GOOGLE_DRIVE_FOLDER_ID, skip Drive upload")
            return False

        # Decodificar credenciales
        import json as js
        if creds_json_b64:
            creds_json_str = base64.b64decode(creds_json_b64).decode('utf-8')
            creds_dict = js.loads(creds_json_str)
        elif creds_json_raw:
            creds_dict = js.loads(creds_json_raw)
        else:
            # Buscar archivo local
            possible_paths = ['/app/google-credentials.json', '/app/equipamientos/google-credentials.json', './google-credentials.json']
            creds_dict = None
            for p in possible_paths:
                if os.path.exists(p):
                    with open(p, 'r') as f:
                        creds_dict = js.load(f)
                    break
            if not creds_dict:
                print("No hay credenciales de Drive")
                return False

        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload

        SCOPES = ['https://www.googleapis.com/auth/drive']
        credentials = service_account.Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        service = build('drive', 'v3', credentials=credentials)

        file_metadata = {
            'name': file_name,
            'parents': [folder_id]
        }
        media = MediaFileUpload(file_path, mimetype='application/gzip', resumable=True)
        file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        print(f"✅ Subido a Drive: {file_name} ID: {file.get('id')}")
        return True

    except Exception as e:
        print(f"⚠️ Error subiendo a Drive (no critico): {e}")
        import traceback; traceback.print_exc()
        return False


class Command(BaseCommand):
    help = 'Backup completo anti-perdida HALCON + Drive'

    def add_arguments(self, parser):
        parser.add_argument('--tipo', type=str, default='AUTO')

    def handle(self, *args, **options):
        tipo = options['tipo']
        self.stdout.write(f"Iniciando backup {tipo}...")
        
        data = {}
        data['fecha'] = timezone.now().isoformat()
        data['productos'] = list(Producto.objects.values())
        data['clientes'] = list(Cliente.objects.values())
        data['ventas'] = list(Venta.objects.values())
        data['item_ventas'] = list(ItemVenta.objects.values())
        data['movimientos_caja'] = list(MovimientoCaja.objects.values())
        data['presupuestos'] = list(Presupuesto.objects.values())
        data['item_presupuestos'] = list(ItemPresupuesto.objects.values())
        # Incluir historial de precios (lo mas valioso)
        try:
            from equipamientos.models import ProductoHistorial
            data['historial_precios'] = list(ProductoHistorial.objects.values()[:1000])
        except:
            data['historial_precios'] = []

        dump_name = f"backup_halcon_{timezone.now().strftime('%Y%m%d_%H%M%S')}_{tipo}.json.gz"
        dump_path = os.path.join('/tmp', dump_name)
        
        json_str = json.dumps(data, default=str, ensure_ascii=False)
        
        with gzip.open(dump_path, 'wt', encoding='utf-8') as f:
            f.write(json_str)

        size_kb = os.path.getsize(dump_path) / 1024

        # Guardar registro en DB
        try:
            from equipamientos.models import BackupAutomatico
            BackupAutomatico.objects.create(
                tipo=tipo,
                archivo_nombre=dump_name,
                archivo_json=json_str[:500000],
                cantidad_productos=len(data['productos']),
                cantidad_ventas=len(data['ventas']),
                cantidad_clientes=len(data['clientes']),
                tamano_kb=size_kb,
                estado='OK',
                nota=f"Backup {tipo} - {len(data['ventas'])} ventas - Drive: intento"
            )
            self.stdout.write(self.style.SUCCESS(f"Backup guardado en DB: {dump_name} - {size_kb:.1f}KB"))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"No se pudo guardar registro en DB: {e}"))

        # Subir a Drive (si esta configurado)
        drive_ok = upload_to_drive(dump_path, dump_name)
        if drive_ok:
            self.stdout.write(self.style.SUCCESS("✅ Backup subido a Google Drive"))
        else:
            self.stdout.write(self.style.WARNING("Backup solo local (configura Drive para externo)"))

        return dump_path
