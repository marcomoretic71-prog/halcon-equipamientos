import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from equipamientos.models import Producto

faltan = Producto.objects.filter(precio=0)
for p in faltan:
    print(f"{p.codigo} | {p.nombre} | {p.categoria}")

print(f"\nTOTAL EN 0: {faltan.count()}")