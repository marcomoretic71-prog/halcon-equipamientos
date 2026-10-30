import json
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Ver cambios por hora - ej: --fecha 2026-10-30 --hora 11'

    def add_arguments(self, parser):
        parser.add_argument('--fecha', type=str, default=None, help='Fecha YYYY-MM-DD, default hoy')
        parser.add_argument('--hora', type=int, default=None, help='Hora 0-23, ej 11 para 11:45')
        parser.add_argument('--minutos', type=int, default=60, help='Ventana en minutos alrededor de la hora, default 60')

    def handle(self, *args, **options):
        from equipamientos.models import Producto
        fecha_str = options['fecha']
        hora = options['hora']
        ventana = options['minutos']

        if fecha_str:
            try:
                fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            except:
                self.stderr.write("Formato fecha YYYY-MM-DD")
                return
        else:
            fecha = timezone.now().date()

        self.stdout.write(f"Buscando cambios del {fecha} " + (f"a las {hora}:00 +- {ventana}min" if hora is not None else "todo el dia"))
        self.stdout.write("")

        # 1. Buscar en ProductoHistorial si existe
        try:
            from equipamientos.models import ProductoHistorial
            qs = ProductoHistorial.objects.filter(fecha__date=fecha).order_by('fecha')
            if hora is not None:
                inicio = datetime.combine(fecha, datetime.min.time()).replace(hour=hora) - timedelta(minutes=ventana)
                fin = datetime.combine(fecha, datetime.min.time()).replace(hour=hora) + timedelta(minutes=ventana)
                inicio = timezone.make_aware(inicio) if timezone.is_naive(inicio) else inicio
                fin = timezone.make_aware(fin) if timezone.is_naive(fin) else fin
                qs = qs.filter(fecha__gte=inicio, fecha__lte=fin)
                self.stdout.write(f"Ventana: {inicio.strftime('%H:%M')} a {fin.strftime('%H:%M')}")
            
            total = qs.count()
            self.stdout.write(f"Registros en ProductoHistorial ese dia/hora: {total}")
            if total == 0:
                self.stdout.write(self.style.WARNING("No hay historial en ProductoHistorial para esa hora"))
            else:
                for h in qs[:100]:
                    prod = h.producto
                    cod = getattr(prod, 'codigo', str(getattr(h, 'producto_id', '?')))
                    nom = getattr(prod, 'nombre', '')
                    accion = getattr(h, 'accion', getattr(h, 'tipo', 'cambio'))
                    ant = getattr(h, 'precio_anterior', getattr(h, 'precio_viejo', ''))
                    nue = getattr(h, 'precio_nuevo', getattr(h, 'precio', ''))
                    stock_ant = getattr(h, 'stock_anterior', '')
                    stock_nue = getattr(h, 'stock_nuevo', '')
                    self.stdout.write(f"  {h.fecha.strftime('%H:%M:%S')} - {cod} | {nom[:40]} | {accion} | Precio {ant} -> {nue} | Stock {stock_ant} -> {stock_nue}")
            self.stdout.write("")
        except Exception as e:
            self.stderr.write(f"Error leyendo ProductoHistorial: {e}")

        # 2. Log de Admin
        try:
            from django.contrib.admin.models import LogEntry
            from django.contrib.contenttypes.models import ContentType
            ct = ContentType.objects.get_for_model(Producto)
            logs = LogEntry.objects.filter(content_type=ct, action_time__date=fecha).order_by('action_time')
            if hora is not None:
                # Filtrar por ventana
                inicio = datetime.combine(fecha, datetime.min.time()).replace(hour=hora) - timedelta(minutes=ventana)
                fin = datetime.combine(fecha, datetime.min.time()).replace(hour=hora) + timedelta(minutes=ventana)
                inicio = timezone.make_aware(inicio) if timezone.is_naive(inicio) else inicio
                fin = timezone.make_aware(fin) if timezone.is_naive(fin) else fin
                logs = logs.filter(action_time__gte=inicio, action_time__lte=fin)
            
            self.stdout.write(f"Log de Admin (cambios en Productos) ventana: {logs.count()} registros")
            for log in logs[:100]:
                self.stdout.write(f"  {log.action_time.strftime('%H:%M:%S')} - Usuario {log.user} - {log.get_action_flag_display()} - {log.object_repr} - {log.change_message[:200]}")
            if logs.count() == 0:
                self.stdout.write("  No hay logs de admin para esa hora - puede que los cambios se hicieron por importacion directa")
            self.stdout.write("")
        except Exception as e:
            self.stderr.write(f"Error leyendo LogEntry: {e}")

        self.stdout.write("--- Productos actuales (ultimos 10 modificados) ---")
        try:
            # Intentar ordenar por fecha_modificacion si existe
            for p in Producto.objects.all().order_by('-id')[:10]:
                stock = getattr(p, 'stock', getattr(p, 'cantidad', getattr(p, 'stock_actual', '?')))
                precio = getattr(p, 'precio', getattr(p, 'precio_venta', '?'))
                fecha_mod = getattr(p, 'fecha_modificacion', getattr(p, 'updated_at', getattr(p, 'fecha_actualizacion', None)))
                self.stdout.write(f"  {p.codigo} | {p.nombre[:40]} | Stock: {stock} | Precio: {precio} | Mod: {fecha_mod}")
        except Exception as e:
            self.stderr.write(f"Error listando productos: {e}")

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Para ver 11:45 de hoy: python manage.py check_cambios_por_hora --fecha 2026-10-30 --hora 11 --minutos 60"))
