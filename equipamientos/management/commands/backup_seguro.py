from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.utils import timezone

class Command(BaseCommand):
    help = 'Backup seguro al abrir/cerrar programa'

    def add_arguments(self, parser):
        parser.add_argument('--evento', type=str, default='CIERRE', choices=['APERTURA','CIERRE','VENTA','PRECIO'], help='Cuando se dispara')

    def handle(self, *args, **options):
        from equipamientos.models import BitacoraDiaria
        evento = options['evento']
        
        self.stdout.write(f"Backup seguro por {evento} - {timezone.now()}")

        # 1. Registrar sesion
        try:
            BitacoraDiaria.objects.create(
                tipo='SESION',
                descripcion=f"{evento} del programa",
            )
        except:
            pass

        # 2. Hacer backup
        try:
            call_command('backup_postgres', tipo='AUTO' if evento in ['APERTURA','CIERRE'] else evento)
            self.stdout.write(self.style.SUCCESS(f"✅ Backup {evento} OK"))
        except Exception as e:
            self.stderr.write(f"Error backup: {e}")

# EN TU PROGRAMA DE ESCRITORIO (el .exe que le vendes al cliente):
# Al ABRIR:
#   python manage.py backup_seguro --evento APERTURA
# Al CERRAR (MUY IMPORTANTE - en el evento on_close de tu ventana):
#   python manage.py backup_seguro --evento CIERRE
# Al hacer una VENTA:
#   python manage.py backup_seguro --evento VENTA  (o que tu codigo llame a Bitacora directo)
# Al cambiar PRECIO/STOCK ya se guarda solo con los signals
