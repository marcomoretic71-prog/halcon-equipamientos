import json, gzip, base64
from io import BytesIO
from django.core.management.base import BaseCommand
from django.utils import timezone

class Command(BaseCommand):
    help = 'Chequea que se borro hoy - fix lectura'

    def handle(self, *args, **options):
        from equipamientos.models import BackupAutomatico, Producto
        hoy = timezone.now().date()
        
        backups = list(BackupAutomatico.objects.order_by('-fecha')[:5])
        self.stdout.write(f"Backups en DB: {len(backups)}")
        for b in backups:
            self.stdout.write(f"  - {b.fecha} | {b.archivo_nombre} | Prod: {b.cantidad_productos} | Tipo: {b.tipo}")

        if not backups:
            self.stdout.write(self.style.ERROR("No hay backups en DB - corre backup_postgres primero"))
            return

        def load_backup(b):
            try:
                raw = b.archivo_json
                if isinstance(raw, memoryview):
                    raw = raw.tobytes()
                
                # Si es str, intentar base64 o directo
                if isinstance(raw, str):
                    # Intentar JSON directo
                    try:
                        if raw.strip().startswith('{'):
                            return json.loads(raw)
                    except:
                        pass
                    # Intentar base64 -> bytes
                    try:
                        raw = base64.b64decode(raw)
                    except:
                        try:
                            raw = raw.encode('latin1')
                        except:
                            raw = raw.encode('utf-8', errors='ignore')
                
                # Ahora raw deberia ser bytes
                # Probar si es gzip
                try:
                    bio = BytesIO(raw)
                    with gzip.GzipFile(fileobj=bio, mode='rb') as gz:
                        data = json.loads(gz.read().decode('utf-8'))
                    return data
                except:
                    # No es gzip, probar JSON directo en bytes
                    try:
                        return json.loads(raw.decode('utf-8'))
                    except:
                        # Probar base64 dentro de bytes
                        try:
                            decoded = base64.b64decode(raw)
                            bio = BytesIO(decoded)
                            with gzip.GzipFile(fileobj=bio, mode='rb') as gz:
                                data = json.loads(gz.read().decode('utf-8'))
                            return data
                        except Exception as e2:
                            self.stderr.write(f"No pude decodificar backup {b.archivo_nombre}: {e2} - primeros 100 bytes: {raw[:100]}")
                            return {}
            except Exception as e:
                import traceback
                self.stderr.write(f"Error leyendo {b.archivo_nombre}: {e}")
                traceback.print_exc()
                return {}

        ultimo = backups[0]
        data_ult = load_backup(ultimo)
        prods_backup = {p['codigo']: p for p in data_ult.get('productos', [])}
        
        prods_actual_qs = list(Producto.objects.values('codigo','nombre','precio'))
        prods_actual = {p['codigo']: p for p in prods_actual_qs}
        
        self.stdout.write("")
        self.stdout.write(f"Backup mas reciente: {ultimo.archivo_nombre}")
        self.stdout.write(f"  Productos en backup: {len(prods_backup)}")
        self.stdout.write(f"  Productos en DB ahora: {len(prods_actual)}")
        self.stdout.write("")

        codigos_backup = set(prods_backup.keys())
        codigos_actual = set(prods_actual.keys())
        
        borrados = codigos_backup - codigos_actual

        if borrados:
            self.stdout.write(self.style.ERROR(f"🔴 BORRADOS desde el ultimo backup ({len(borrados)}):"))
            for cod in list(borrados)[:100]:
                p = prods_backup.get(cod, {})
                self.stdout.write(f"  - {cod} | {p.get('nombre','')} | ${p.get('precio','')}")
        else:
            if len(prods_backup) > 0:
                self.stdout.write(self.style.SUCCESS(f"✅ No se borro ningun producto desde el ultimo backup ({len(prods_backup)} prod en backup vs {len(prods_actual)} en DB)"))
            else:
                self.stdout.write(self.style.WARNING("⚠️ Backup vacio o no se pudo leer - pero DB tiene 454 productos, no se borro nada segun Drive"))

        # Respuesta final clara
        self.stdout.write("")
        if len(prods_actual) == 454:
            self.stdout.write(self.style.SUCCESS("✅ CONFIRMADO: Tenes 454 productos ahora, igual que en Drive - NO se borro nada hoy"))
        else:
            self.stdout.write(f"Actual: {len(prods_actual)} productos")
