from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

class DatosEmpresa(models.Model):
    direccion = models.CharField(max_length=200, default="Ruta 89 Km. Quimili, SGO")
    whatsapp = models.CharField(max_length=100, default="2983512672 / 3843400199")
    instagram = models.CharField(max_length=100, default="halcon_equipamientos")
    alias = models.CharField(max_length=100, default="halconequipamientos")
    condiciones = models.CharField(max_length=200, default="Se reserva con seña del 10%. Validez 15 dias.")
    def __str__(self): return self.direccion

class Cliente(models.Model):
    nombre = models.CharField(max_length=150)
    telefono = models.CharField(max_length=50, blank=True)
    vehiculo_anio = models.CharField(max_length=100, blank=True)
    creado = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.nombre

class Producto(models.Model):
    codigo = models.CharField(max_length=50, unique=True, verbose_name="Código interno")
    barcode = models.CharField(max_length=100, blank=True, null=True, unique=True, verbose_name="Código de Barras")
    nombre = models.CharField(max_length=250)
    categoria = models.CharField(max_length=50, default="OTRO")
    precio = models.DecimalField(max_digits=12, decimal_places=2)
    stock = models.IntegerField(default=0)
    fecha_ultimo_cambio_precio = models.DateTimeField(null=True, blank=True, verbose_name="Último cambio precio")
    fecha_ultimo_cambio_stock = models.DateTimeField(null=True, blank=True, verbose_name="Último cambio stock")
    # === CAMPOS NUEVOS SISTEMA SEGURO ===
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True)
    fecha_modificacion = models.DateTimeField(auto_now=True, null=True, db_index=True)
    modificado_por = models.CharField(max_length=100, blank=True, null=True)
    def __str__(self):
        return f"{self.nombre} ({self.codigo})"

class ListaPrecio(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    porcentaje = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    activa = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    def __str__(self): return f"{self.nombre} ({self.porcentaje}%)"

class ItemListaPrecio(models.Model):
    lista = models.ForeignKey(ListaPrecio, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    precio = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    class Meta:
        unique_together = ('lista', 'producto')

class Presupuesto(models.Model):
    codigo = models.CharField(max_length=20, unique=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT)
    vehiculo = models.CharField(max_length=100, blank=True)
    colocacion = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Mano de obra / Instalación")
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    creado = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.codigo

class ItemPresupuesto(models.Model):
    presupuesto = models.ForeignKey(Presupuesto, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='items_presupuesto')
    cantidad = models.IntegerField(default=1)
    precio = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    def save(self, *args, **kwargs):
        if self.precio and not self.precio_unitario:
            self.precio_unitario = self.precio
        if self.precio_unitario and not self.precio:
            self.precio = self.precio_unitario
        super().save(*args, **kwargs)

class Venta(models.Model):
    FORMA_PAGO_CHOICES = [
        ('EFECTIVO', 'Efectivo'),
        ('TRANSFERENCIA', 'Transferencia'),
        ('TARJETA', 'Tarjeta'),
        ('CUENTA_CORRIENTE', 'Cuenta Corriente'),
        ('MERCADOPAGO', 'MercadoPago'),
    ]
    codigo = models.CharField(max_length=20, unique=True)
    presupuesto = models.OneToOneField(Presupuesto, on_delete=models.SET_NULL, null=True, blank=True, related_name='venta')
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT)
    vehiculo = models.CharField(max_length=100, blank=True)
    colocacion = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Mano de obra / Instalación")
    total = models.DecimalField(max_digits=12, decimal_places=2)
    forma_pago = models.CharField(max_length=20, choices=FORMA_PAGO_CHOICES, default='EFECTIVO')
    fecha_venta = models.DateTimeField(auto_now_add=True)
    stock_descontado = models.BooleanField(default=False)
    es_directa = models.BooleanField(default=False, help_text="True si es venta sin presupuesto")
    creado = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    descuento_porcentaje = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Descuento % sobre productos")
    descuento_monto = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Monto descontado")
    subtotal_productos = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Subtotal productos sin descuento")
    total_original = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Total original sin descuento")
    class Meta:
        ordering = ['-fecha_venta']
    def __str__(self): return f"{self.codigo} - {self.cliente.nombre}"

class ItemVenta(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='items_venta', null=True, blank=True)
    cantidad = models.IntegerField(default=1)
    precio = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    es_manual = models.BooleanField(default=False, verbose_name="Es producto manual sin stock")
    nombre_manual = models.CharField(max_length=250, blank=True, default="", verbose_name="Nombre manual")
    def __str__(self):
        if self.es_manual:
            return f"{self.venta.codigo} - MANUAL {self.nombre_manual} x{self.cantidad}"
        return f"{self.venta.codigo} - {self.producto.codigo if self.producto else 'SIN PROD'} x{self.cantidad}"

class MovimientoCaja(models.Model):
    TIPO_CHOICES = [('INGRESO','Ingreso'),('EGRESO','Egreso')]
    fecha = models.DateTimeField(auto_now_add=True)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    concepto = models.CharField(max_length=200)
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    forma_pago = models.CharField(max_length=20, default='EFECTIVO')
    venta = models.ForeignKey('Venta', null=True, blank=True, on_delete=models.SET_NULL)
    nota = models.TextField(blank=True)
    def __str__(self):
        return f"{self.tipo} - {self.concepto} ${self.monto}"

class EmpresaCliente(models.Model):
    nombre = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    contacto = models.CharField(max_length=200, blank=True)
    whatsapp = models.CharField(max_length=50, blank=True)
    activo = models.BooleanField(default=True)
    bloqueado = models.BooleanField(default=False)
    motivo_bloqueo = models.CharField(max_length=300, blank=True, default="Cuota vencida - Contactar a soporte")
    plan = models.CharField(max_length=50, default="MENSUAL", choices=[('MENSUAL','Mensual'),('ANUAL','Anual'),('PRUEBA','Prueba')])
    fecha_alta = models.DateTimeField(auto_now_add=True)
    fecha_vencimiento = models.DateField(null=True, blank=True)
    precio_mensual = models.DecimalField(max_digits=10, decimal_places=2, default=15000)
    notas_privadas = models.TextField(blank=True)
    def __str__(self):
        return f"{self.nombre} - {'BLOQUEADO' if self.bloqueado else 'ACTIVO'}"
    @property
    def dias_restantes(self):
        if not self.fecha_vencimiento:
            return 999
        from datetime import date
        delta = self.fecha_vencimiento - date.today()
        return delta.days

class RegistroAcceso(models.Model):
    empresa = models.ForeignKey(EmpresaCliente, on_delete=models.CASCADE, null=True, blank=True)
    usuario = models.CharField(max_length=100)
    accion = models.CharField(max_length=200)
    ip = models.GenericIPAddressField(null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.fecha.strftime('%d/%m %H:%M')} - {self.usuario} - {self.accion}"

class ConfigSistema(models.Model):
    bloqueado_global = models.BooleanField(default=False)
    mensaje_bloqueo = models.CharField(max_length=300, default="Sistema en mantenimiento - Contactar a Halcon Sistemas 2983-512672")
    version = models.CharField(max_length=20, default="2.1")
    def __str__(self):
        return f"Config v{self.version} - {'BLOQUEADO' if self.bloqueado_global else 'OK'}"


class BackupAutomatico(models.Model):
    fecha = models.DateTimeField(default=timezone.now)
    tipo = models.CharField(max_length=20, default='AUTO')
    archivo_nombre = models.CharField(max_length=255)
    archivo_json = models.TextField(blank=True)
    cantidad_productos = models.IntegerField(default=0)
    cantidad_ventas = models.IntegerField(default=0)
    cantidad_clientes = models.IntegerField(default=0)
    tamano_kb = models.FloatField(default=0)
    estado = models.CharField(max_length=20, default='OK')
    nota = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['-fecha']
    
    def __str__(self):
        return f"{self.fecha.strftime('%d/%m %H:%M')} - {self.tipo} - V:{self.cantidad_ventas} P:{self.cantidad_productos}"

class ProductoHistorial(models.Model):
    producto = models.ForeignKey('Producto', on_delete=models.CASCADE, related_name='historial', null=True)
    codigo = models.CharField(max_length=100)
    nombre = models.CharField(max_length=300, blank=True)
    campo = models.CharField(max_length=20)
    valor_viejo = models.CharField(max_length=100, blank=True)
    valor_nuevo = models.CharField(max_length=100)
    usuario = models.CharField(max_length=100, default='cliente')
    fecha = models.DateTimeField(default=timezone.now)
    ip = models.CharField(max_length=50, blank=True)

    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.fecha.strftime('%d/%m %H:%M')} - {self.codigo} {self.campo}: {self.valor_viejo} -> {self.valor_nuevo}"


class BitacoraDiaria(models.Model):
    TIPO_CHOICES = [
        ('PRECIO', 'Cambio Precio'),
        ('STOCK', 'Cambio Stock'),
        ('VENTA', 'Venta'),
        ('PRODUCTO_NUEVO', 'Producto Nuevo'),
        ('PRODUCTO_BORRADO', 'Producto Borrado'),
        ('CLIENTE', 'Cambio Cliente'),
        ('CAJA', 'Movimiento Caja'),
        ('IMPORT', 'Importacion Excel'),
        ('BACKUP', 'Backup'),
        ('SESION', 'Inicio/Cierre Sesion'),
    ]
    fecha = models.DateTimeField(auto_now_add=True, db_index=True)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, db_index=True)
    usuario = models.CharField(max_length=100, blank=True, null=True)
    codigo_producto = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    nombre_producto = models.CharField(max_length=255, blank=True, null=True)
    datos_anterior = models.JSONField(blank=True, null=True)
    datos_nuevo = models.JSONField(blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-fecha']
        indexes = [
            models.Index(fields=['fecha', 'tipo']),
            models.Index(fields=['codigo_producto', 'fecha']),
        ]
    
    def __str__(self):
        return f"{self.fecha.strftime('%d/%m %H:%M')} - {self.tipo} - {self.codigo_producto} - {self.descripcion}"
