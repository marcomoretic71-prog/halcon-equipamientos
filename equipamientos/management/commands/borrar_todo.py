from django.core.management.base import BaseCommand
from equipamientos.models import Producto, ListaPrecio, ItemListaPrecio, Presupuesto, ItemPresupuesto, Cliente

class Command(BaseCommand):
    help = 'Borra TODOS los datos para dejar el sistema en cero'

    def handle(self, *args, **kwargs):
        print("\n⚠️  ESTÁS POR BORRAR TODO:")
        print(f" - Productos: {Producto.objects.count()}")
        print(f" - Listas: {ListaPrecio.objects.count()}")
        print(f" - Items de listas: {ItemListaPrecio.objects.count()}")
        print(f" - Presupuestos: {Presupuesto.objects.count()}")
        print(f" - Clientes: {Cliente.objects.count()}")
        
        confirm = input("\nEscribí SI para borrar todo: ")

        if confirm != "SI":
            self.stdout.write(self.style.WARNING("Cancelado. No se borró nada."))
            return

        # Orden importante por relaciones
        ItemPresupuesto.objects.all().delete()
        Presupuesto.objects.all().delete()
        ItemListaPrecio.objects.all().delete()
        ListaPrecio.objects.all().delete()
        Producto.objects.all().delete()
        Cliente.objects.all().delete()

        self.stdout.write(self.style.SUCCESS("\n✅ TODO BORRADO. Base de datos en cero."))
        self.stdout.write(self.style.SUCCESS("Ahora podés correr: python manage.py importar_halcon"))