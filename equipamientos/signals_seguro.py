from django.db.models.signals import pre_save, post_save, pre_delete, post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from .models import Producto, Venta, BitacoraDiaria
import threading

# Thread-local para contar borrados por request
_thread_locals = threading.local()

def get_borrados_count():
    return getattr(_thread_locals, 'borrados_count', 0)

def set_borrados_count(val):
    _thread_locals.borrados_count = val

def increment_borrados():
    count = get_borrados_count() + 1
    set_borrados_count(count)
    return count

@receiver(pre_save, sender=Producto)
def producto_cambio_seguro(sender, instance, **kwargs):
    if not instance.pk:
        return
    try:
        anterior = Producto.objects.get(pk=instance.pk)
        if anterior.precio != instance.precio:
            BitacoraDiaria.objects.create(
                tipo='PRECIO',
                codigo_producto=instance.codigo,
                nombre_producto=instance.nombre,
                datos_anterior={'precio': str(anterior.precio)},
                datos_nuevo={'precio': str(instance.precio)},
                descripcion=f"Precio {anterior.precio} -> {instance.precio}",
                usuario=getattr(instance, 'modificado_por', 'sistema')
            )
        stock_ant = getattr(anterior, 'stock', None)
        stock_nue = getattr(instance, 'stock', None)
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
    except:
        pass

@receiver(post_save, sender=Producto)
def producto_nuevo_seguro(sender, instance, created, **kwargs):
    if created:
        try:
            BitacoraDiaria.objects.create(
                tipo='PRODUCTO_NUEVO',
                codigo_producto=instance.codigo,
                nombre_producto=instance.nombre,
                datos_nuevo={'precio': str(instance.precio)},
                descripcion=f"Nuevo producto {instance.codigo}",
            )
        except:
            pass
    # Resetear contador después de crear (nuevo request)
    set_borrados_count(0)

@receiver(pre_delete, sender=Producto)
def producto_borrado_seguro(sender, instance, **kwargs):
    # BLOQUEO AUTOMÁTICO DE BORRADOS MASIVOS
    count = increment_borrados()
    
    # Si intentan borrar más de 10 productos en la misma operación, BLOQUEAR
    if count > 10:
        try:
            BitacoraDiaria.objects.create(
                tipo='PRODUCTO_BORRADO',
                codigo_producto='BLOQUEO_MASIVO',
                nombre_producto=f'INTENTO BORRADO MASIVO BLOQUEADO: {count} productos',
                descripcion=f'BLOQUEO AUTOMÁTICO: Intento de borrar {count} productos bloqueado',
            )
        except:
            pass
        # Resetear para próximo intento
        set_borrados_count(0)
        raise PermissionDenied(f"BLOQUEO AUTOMÁTICO: Intento de borrar {count} productos bloqueado. Si realmente querés borrar masivo, borrá de a 10 por vez máximo.")
    
    try:
        BitacoraDiaria.objects.create(
            tipo='PRODUCTO_BORRADO',
            codigo_producto=instance.codigo,
            nombre_producto=instance.nombre,
            datos_anterior={'precio': str(instance.precio)},
            descripcion=f"Borrado {instance.codigo}",
        )
    except:
        pass

@receiver(post_save, sender=Venta)
def venta_segura(sender, instance, created, **kwargs):
    if created:
        try:
            BitacoraDiaria.objects.create(
                tipo='VENTA',
                datos_nuevo={'venta_id': instance.id, 'total': str(getattr(instance, 'total', ''))},
                descripcion=f"Venta #{instance.id} - ${getattr(instance, 'total', '')}",
            )
        except:
            pass