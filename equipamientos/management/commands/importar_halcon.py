import os
import pandas as pd
import math
from django.core.management.base import BaseCommand
from equipamientos.models import Producto, ListaPrecio, ItemListaPrecio

def clean_float(v):
    try:
        if pd.isna(v):
            return 0.0
        f = float(v)
        if math.isnan(f):
            return 0.0
        return f
    except:
        return 0.0

def clean_int(v):
    try:
        if pd.isna(v):
            return 1
        return int(float(v))
    except:
        return 1

class Command(BaseCommand):
    help = 'Importa INVENTARIO_HALCON.xlsx SIN BORRAR PRECIOS existentes'

    def handle(self, *args, **kwargs):
        posibles_rutas = [
            'INVENTARIO_HALCON.xlsx',
            'INVENTARIO HALCON.xlsx',
            'inventario_halcon.xlsx',
        ]
        ruta = None
        for r in posibles_rutas:
            if os.path.exists(r):
                ruta = r
                break
        if not ruta:
            self.stdout.write(self.style.ERROR('No encuentro el Excel'))
            return

        xls = pd.ExcelFile(ruta)
        total_creados = 0
        total_actualizados = 0
        total_preservados = 0

        self.stdout.write(f"Encontrado: {ruta} - Hojas {xls.sheet_names}")

        for sheet in xls.sheet_names:
            if sheet.lower() in ['copiar', 'ajustes']:
                continue

            df_raw = xls.parse(sheet, header=None)
            header_idx = None
            for i in range(min(30, len(df_raw))):
                vals = [str(v).strip().upper() for v in df_raw.iloc[i].values]
                if 'CODIGO' in vals and 'PRODUCTO' in vals:
                    header_idx = i
                    break
            if header_idx is None:
                continue

            df = xls.parse(sheet, header=header_idx)
            df.columns = [str(c).strip().upper() for c in df.columns]

            nombre_lista = f"{sheet.upper()} - Base"
            lista, _ = ListaPrecio.objects.get_or_create(
                nombre=nombre_lista,
                defaults={'descripcion': f'Importado desde {sheet}'}
            )

            for _, row in df.iterrows():
                codigo = str(row.get('CODIGO','')).strip()
                if not codigo or codigo.upper() == 'CODIGO' or codigo.lower() == 'nan':
                    continue
                if codigo.endswith('.0'):
                    codigo = codigo[:-2]

                nombre = str(row.get('PRODUCTO','')).strip()
                if not nombre or nombre.lower() == 'nan':
                    nombre = codigo

                fabrica = clean_float(row.get('FABRICA', 0))
                publico = clean_float(row.get('PUBLICO', 0))
                stock = clean_int(row.get('STOCK', 0))

                precio_final = publico if publico > 0 else (fabrica if fabrica > 0 else 0.0)

                try:
                    prod_existente = Producto.objects.filter(codigo=codigo).first()

                    if prod_existente and precio_final == 0 and prod_existente.precio > 0:
                        # PRESERVAMOS PRECIO EXISTENTE
                        precio_a_usar = float(prod_existente.precio)
                        total_preservados += 1
                    else:
                        precio_a_usar = precio_final

                    prod, creado = Producto.objects.update_or_create(
                        codigo=codigo,
                        defaults={
                            'nombre': nombre[:300],
                            'precio': precio_a_usar if precio_a_usar > 0 else (prod_existente.precio if prod_existente else 0),
                            'costo_fabrica': fabrica if fabrica > 0 else (prod_existente.costo_fabrica if prod_existente else 0),
                            'stock': stock,
                            'categoria': sheet.upper(),
                            'compatibilidad': nombre[:300]
                        }
                    )

                    # Si el item de lista ya tiene precio y el nuevo es 0, no lo pisamos
                    item_existente = ItemListaPrecio.objects.filter(lista=lista, producto=prod).first()
                    if item_existente and precio_a_usar == 0 and item_existente.precio > 0:
                        precio_item = float(item_existente.precio)
                    else:
                        precio_item = precio_a_usar if precio_a_usar > 0 else float(prod.precio)

                    ItemListaPrecio.objects.update_or_create(
                        lista=lista, producto=prod,
                        defaults={'precio': precio_item}
                    )
                    if creado: total_creados += 1
                    else: total_actualizados += 1
                except Exception as e:
                    self.stdout.write(f"Error fila {codigo}: {e}")

        self.stdout.write(self.style.SUCCESS(f'Listo! Creados: {total_creados} | Actualizados: {total_actualizados} | Preservados (no pisados por 0): {total_preservados}'))