import json, gzip
from io import BytesIO
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = 'Chequea que se borro hoy comparando ultimos 2 backups'

    def handle(self, *args, **options):
        from equipamientos.models import BackupAutomatico, Producto
        hoy = timezone.now().date()
        ayer = hoy - timedelta(days=1)
        
        backups = list(BackupAutomatico.objects.order_by('-fecha')[:5])
        if len(backups) < 2:
            self.stdout.write("Solo hay 1 backup, no puedo comparar. Tenes backup de hoy y de ayer?")
            # igual listamos lo de hoy
            backups = list(BackupAutomatico.objects.filter(fecha__date=hoy).order_by('-fecha'))
            if backups:
                self.stdout.write(f"Backup de hoy: {backups[0].archivo_nombre} - Prod: {backups[0].cantidad_productos}")
            return

        # Descomprimir ultimos 2
        def load_backup(b):
            try:
                raw = b.archivo_json
                if isinstance(raw, memoryview):
                    raw = raw.tobytes()
                bio = BytesIO(raw)
                with gzip.GzipFile(fileobj=bio, mode='rb') as gz:
                    data = json.loads(gz.read().decode('utf-8'))
                return data
            except Exception as e:
                self.stderr.write(f"Error leyendo {b.archivo_nombre}: {e}")
                return {}

        ultimo = backups[0]
        anterior = backups[1]
        
        self.stdout.write(f"Comparando:")
        self.stdout.write(f"  ANTERIOR: {anterior.archivo_nombre} - {anterior.fecha} - Prod: {anterior.cantidad_productos}")
        self.stdout.write(f"  ULTIMO:   {ultimo.archivo_nombre} - {ultimo.fecha} - Prod: {ultimo.cantidad_productos}")
        
        data_ult = load_backup(ultimo)
        data_ant = load_backup(anterior)
        
        prods_ult = {p['codigo']: p for p in data_ult.get('productos', [])}
        prods_ant = {p['codigo']: p for p in data_ant.get('productos', [])}
        
        codigos_ult = set(prods_ult.keys())
        codigos_ant = set(prods_ant.keys())
        
        borrados = codigos_ant - codigos_ult
        agregados = codigos_ult - codigos_ant
        
        self.stdout.write("")
        if borrados:
            self.stdout.write(self.style.ERROR(f"🔴 BORRADOS HOY ({len(borrados)}):"))
            for cod in list(borrados)[:50]:
                p = prods_ant.get(cod, {})
                self.stdout.write(f"  - {cod} | {p.get('nombre','')} | ${p.get('precio','')}")
            if len(borrados) > 50:
                self.stdout.write(f"  ... y {len(borrados)-50} mas")
        else:
            self.stdout.write(self.style.SUCCESS("✅ No se borro ningun producto entre los ultimos 2 backups"))
        
        self.stdout.write("")
        if agregados:
            self.stdout.write(self.style.SUCCESS(f"🟢 AGREGADOS ({len(agregados)}):"))
            for cod in list(agregados)[:20]:
                p = prods_ult.get(cod, {})
                self.stdout.write(f"  + {cod} | {p.get('nombre','')}")

        # Chequear Productos actuales vs backup
        self.stdout.write("")
        self.stdout.write("--- Estado actual en DB ---")
        total_actual = Producto.objects.count()
        self.stdout.write(f"Productos en DB ahora: {total_actual}")
        
        # Chequear si hubo borrados via ProductoHistorial si existe
        try:
            from equipamientos.models import ProductoHistorial
            hoy_historial = ProductoHistorial.objects.filter(fecha__date=hoy).order_by('-fecha')[:20]
            if hoy_historial:
                self.stdout.write("")
                self.stdout.write(f"Historial de hoy ({hoy}):")
                for h in hoy_historial:
                    self.stdout.write(f"  {h.fecha} - {h.producto.codigo} - {h.accion} - {h.precio_anterior} -> {h.precio_nuevo}")
        except:
            pass
