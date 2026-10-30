from django.db.models.signals import pre_save, post_save, pre_delete
from django.dispatch import receiver
from django.utils import timezone
from .models import Producto, Venta, ItemVenta, MovimientoCaja, BitacoraDiaria
import json

@receiver(pre_save, sender=Producto)
def producto_cambio_seguro(sender, instance, **kwargs):
    """Antes de guardar, si cambio precio o stock, guarda en Bitacora"""
    if not instance.pk:
        return  # es nuevo, lo maneja post_save
    
    try:
        anterior = Producto.objects.get(pk=instance.pk)
        cambios = []
        
        # Precio
        if anterior.precio != instance.precio:
            cambios.append(f"Precio {anterior.precio} -> {instance.precio}")
            BitacoraDiaria.objects.create(
                tipo='PRECIO',
                codigo_producto=instance.codigo,
                nombre_producto=instance.nombre,
                datos_anterior={'precio': str(anterior.precio), 'stock': str(getattr(anterior, 'stock', ''))},
                datos_nuevo={'precio': str(instance.precio), 'stock': str(getattr(instance, 'stock', ''))},
                descripcion=f"Precio {anterior.precio} -> {instance.precio}",
                usuario=getattr(instance, 'modificado_por', 'sistema')
            )
        
        # Stock
        stock_ant = getattr(anterior, 'stock', getattr(anterior, 'cantidad', None))
        stock_nue = getattr(instance, 'stock', getattr(instance, 'cantidad', None))
        if stock_ant != stock_nue:
            BitacoraDiaria.objects.create(
                tipo='STOCK',
                codigo_producto=instance.codigo,
                nombre_producto=instance.nombre,
                datos_anterior={'stock': str(stock_ant)},
                datos_nuevo={'stock': str(stock_nue)},
                descripcion=f"Stock {stock_ant} -> {stock_nue}",
                usuario=getattr(instance, 'modificado_por', 'sistema')
            )
    except Producto.DoesNotExist:
        pass
    except Exception as e:
        print(f"Error signal producto: {e}")

@receiver(post_save, sender=Producto)
def producto_nuevo_seguro(sender, instance, created, **kwargs):
    if created:
        try:
            BitacoraDiaria.objects.create(
                tipo='PRODUCTO_NUEVO',
                codigo_producto=instance.codigo,
                nombre_producto=instance.nombre,
                datos_nuevo={'precio': str(instance.precio), 'stock': str(getattr(instance, 'stock', ''))},
                descripcion=f"Nuevo producto {instance.codigo}",
            )
        except Exception as e:
            print(f"Error signal nuevo: {e}")

@receiver(pre_delete, sender=Producto)
def producto_borrado_seguro(sender, instance, **kwargs):
    try:
        BitacoraDiaria.objects.create(
            tipo='PRODUCTO_BORRADO',
            codigo_producto=instance.codigo,
            nombre_producto=instance.nombre,
            datos_anterior={'precio': str(instance.precio), 'stock': str(getattr(instance, 'stock', ''))},
            descripcion=f"Borrado {instance.codigo}",
        )
    except Exception as e:
        print(f"Error signal borrado: {e}")

@receiver(post_save, sender=Venta)
def venta_segura(sender, instance, created, **kwargs):
    if created:
        try:
            BitacoraDiaria.objects.create(
                tipo='VENTA',
                datos_nuevo={'venta_id': instance.id, 'total': str(getattr(instance, 'total', ''))},
                descripcion=f"Venta #{instance.id} - ${getattr(instance, 'total', '')}",
            )
        except Exception as e:
            print(f"Error signal venta: {e}")

# IMPORTANTE: En equipamientos/apps.py agregar:
# def ready(self):
#     import equipamientos.signals_seguro
