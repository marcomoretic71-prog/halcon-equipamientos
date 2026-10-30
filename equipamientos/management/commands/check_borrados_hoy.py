import json, gzip
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

        # Cargar ultimo backup
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
            if len(borrados) > 100:
                self.stdout.write(f"  ... y {len(borrados)-100} mas")
        else:
            self.stdout.write(self.style.SUCCESS("✅ No se borro ningun producto desde el ultimo backup"))

        self.stdout.write("")
        if agregados:
            self.stdout.write(self.style.SUCCESS(f"🟢 AGREGADOS desde ultimo backup ({len(agregados)}):"))
            for cod in list(agregados)[:20]:
                p = prods_actual.get(cod, {})
                self.stdout.write(f"  + {cod} | {p.get('nombre','')} | ${p.get('precio','')}")

        # Revisar si hubo cambios hoy en ProductoHistorial
        try:
            from equipamientos.models import ProductoHistorial
            hoy_hist = list(ProductoHistorial.objects.filter(fecha__date=hoy).order_by('-fecha')[:30])
            if hoy_hist:
                self.stdout.write("")
                self.stdout.write(f"📜 Historial de precios de HOY {hoy}:")
                for h in hoy_hist:
                    prod_code = getattr(h.producto, 'codigo', str(h.producto_id))
                    self.stdout.write(f"  {h.fecha.strftime('%H:%M')} - {prod_code} - {h.accion if hasattr(h,'accion') else ''} {getattr(h,'precio_anterior','')} -> {getattr(h,'precio_nuevo','')}")
        except Exception as e:
            self.stdout.write(f"Sin historial o error: {e}")
