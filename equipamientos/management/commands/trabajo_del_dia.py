from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Ver todo lo que hizo el cliente en el dia - ventas, precios, stock'

    def add_arguments(self, parser):
        parser.add_argument('--fecha', type=str, default=None, help='YYYY-MM-DD default hoy')
        parser.add_argument('--codigo', type=str, default=None, help='Filtrar por codigo producto')

    def handle(self, *args, **options):
        from equipamientos.models import BitacoraDiaria, Producto, Venta
        fecha_str = options['fecha']
        if fecha_str:
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        else:
            fecha = timezone.now().date()

        qs = BitacoraDiaria.objects.filter(fecha__date=fecha).order_by('fecha')
        if options['codigo']:
            qs = qs.filter(codigo_producto=options['codigo'])

        self.stdout.write(f"\n=== TRABAJO DEL DIA {fecha} ===")
        self.stdout.write(f"Total acciones: {qs.count()}")
        
        for tipo in ['SESION','VENTA','PRECIO','STOCK','PRODUCTO_NUEVO','PRODUCTO_BORRADO','IMPORT','CAJA']:
            count = qs.filter(tipo=tipo).count()
            if count:
                self.stdout.write(f"  {tipo}: {count}")

        self.stdout.write("\n--- Detalle por hora ---")
        for log in qs[:200]:
            self.stdout.write(f"{log.fecha.strftime('%H:%M:%S')} | {log.tipo:15} | {log.codigo_producto or '-':15} | {log.descripcion} | {log.datos_anterior} -> {log.datos_nuevo}")

        # Resumen ventas
        ventas_hoy = qs.filter(tipo='VENTA').count()
        self.stdout.write(f"\nVentas hoy: {ventas_hoy}")

        # Si no hay bitacora, mostrar mensaje
        if qs.count() == 0:
            self.stdout.write(self.style.WARNING("\n⚠️ No hay registros de hoy - El sistema seguro aun no esta instalado"))
            self.stdout.write("Instala los signals para que empiece a registrar")

        self.stdout.write("\n=== FIN ===\n")
