import json, gzip, base64
from io import BytesIO
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = 'Chequea que se borro hoy'

    def handle(self, *args, **options):
        from equipamientos.models import BackupAutomatico, Producto
        hoy = timezone.now().date()
        
        backups = list(BackupAutomatico.objects.order_by('-fecha')[:5])
        self.stdout.write(f"Backups en DB: {len(backups)}")
        for b in backups:
            self.stdout.write(f"  - {b.fecha} | {b.archivo_nombre} | Prod: {b.cantidad_productos} | Tipo: {b.tipo}")

        if not backups:
            self.stdout.write(self.style.ERROR("No hay backups en DB"))
            return

        def load_backup(b):
            try:
                raw = b.archivo_json
                # Normalizar a bytes
                if isinstance(raw, memoryview):
                    raw = raw.tobytes()
                elif isinstance(raw, str):
                    # Puede venir como base64 o como latin1
                    try:
                        raw = base64.b64decode(raw)
                    except:
                        try:
                            raw = raw.encode('latin1')
                        except:
                            raw = raw.encode('utf-8', errors='ignore')
                
                bio = BytesIO(raw)
                with gzip.GzipFile(fileobj=bio, mode='rb') as gz:
                    data = json.loads(gz.read().decode('utf-8'))
                return data
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
        agregados = codigos_actual - codigos_backup

        if borrados:
            self.stdout.write(self.style.ERROR(f"🔴 BORRADOS desde el ultimo backup ({len(borrados)}):"))
            for cod in list(borrados)[:100]:
                p = prods_backup.get(cod, {})
                self.stdout.write(f"  - {cod} | {p.get('nombre','')} | ${p.get('precio','')}")
        else:
            self.stdout.write(self.style.SUCCESS("✅ No se borro ningun producto desde el ultimo backup"))

        self.stdout.write("")
        if agregados:
            self.stdout.write(f"🟢 AGREGADOS desde ultimo backup ({len(agregados)}): solo muestra si hubo error de lectura, ignora si es 0")

        # Chequear si hay 2 backups para comparar hoy vs ayer
        if len(backups) >= 2:
            anterior = backups[1]
            data_ant = load_backup(anterior)
            prods_ant = {p['codigo']: p for p in data_ant.get('productos', [])}
            cod_ant = set(prods_ant.keys())
            cod_ult = set(prods_backup.keys())
            borr_ayer_hoy = cod_ant - cod_ult
            if borr_ayer_hoy:
                self.stdout.write("")
                self.stdout.write(self.style.ERROR(f"🔴 BORRADOS entre backup anterior y ultimo ({len(borr_ayer_hoy)}):"))
                for cod in list(borr_ayer_hoy)[:50]:
                    p = prods_ant.get(cod, {})
                    self.stdout.write(f"  - {cod} | {p.get('nombre','')}")
            else:
                self.stdout.write("")
                self.stdout.write(self.style.SUCCESS("✅ Entre los ultimos 2 backups no se borro nada"))
