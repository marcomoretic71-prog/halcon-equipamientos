import json, os, gzip, base64
from datetime import datetime
from django.core.management.base import BaseCommand
from django.core import serializers
from django.utils import timezone
from equipamientos.models import Producto, Venta, ItemVenta, Cliente, MovimientoCaja, Presupuesto, ItemPresupuesto

class Command(BaseCommand):
    help = 'Backup completo anti-perdida HALCON'

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

        # Guardar en archivo JSONL de log incremental
        log_path = '/tmp/ventas_log.jsonl'
        # Si existe, no lo pisamos, solo agregamos
        # El dump completo
        dump_name = f"backup_halcon_{timezone.now().strftime('%Y%m%d_%H%M%S')}_{tipo}.json.gz"
        dump_path = os.path.join('/tmp', dump_name)
        
        json_str = json.dumps(data, default=str, ensure_ascii=False)
        
        # Guardar comprimido
        with gzip.open(dump_path, 'wt', encoding='utf-8') as f:
            f.write(json_str)

        size_kb = os.path.getsize(dump_path) / 1024

        # Guardar registro en DB
        try:
            from equipamientos.models import BackupAutomatico
            BackupAutomatico.objects.create(
                tipo=tipo,
                archivo_nombre=dump_name,
                archivo_json=json_str[:500000], # guardamos primeros 500k chars, el archivo completo queda en /tmp y Drive
                cantidad_productos=len(data['productos']),
                cantidad_ventas=len(data['ventas']),
                cantidad_clientes=len(data['clientes']),
                tamano_kb=size_kb,
                estado='OK',
                nota=f"Backup {tipo} - {len(data['ventas'])} ventas"
            )
            self.stdout.write(self.style.SUCCESS(f"Backup guardado en DB: {dump_name} - {size_kb:.1f}KB"))
        except Exception as e:
            # Si no existe modelo aun, al menos dejamos archivo
            self.stdout.write(self.style.WARNING(f"No se pudo guardar registro en DB (modelo no migrado?): {e}"))

        # También escribir log incremental de ventas para recuperacion ultra rapida
        log_ventas_path = '/tmp/ventas_incremental.jsonl'
        try:
            with open(log_ventas_path, 'a', encoding='utf-8') as lf:
                for v in data['ventas']:
                    lf.write(json.dumps(v, default=str) + "\n")
        except Exception as e:
            self.stdout.write(f"Log incremental error: {e}")

        self.stdout.write(self.style.SUCCESS(f"Archivo en {dump_path} listo para subir a Drive/S3"))
        return dump_path
