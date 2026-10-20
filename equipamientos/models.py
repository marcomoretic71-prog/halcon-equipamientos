from django.db import models

class ProductoActivoManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(es_activo=True)

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
    # === BLINDAJE SOFT DELETE ===
    es_activo = models.BooleanField(default=True, db_index=True, help_text="False = desactivado, no se borra nunca")
    eliminado_en = models.DateTimeField(null=True, blank=True)
    eliminado_por = models.CharField(max_length=100, blank=True, default="")

    objects = models.Manager()
    activos = ProductoActivoManager()

    def __str__(self):
        return f"{self.nombre} ({self.codigo})" + ("" if self.es_activo else " [INACTIVO]")

    def desactivar(self, usuario="sistema"):
        from django.utils import timezone
        self.es_activo = False
        self.eliminado_en = timezone.now()
        self.eliminado_por = usuario
        self.save(update_fields=['es_activo','eliminado_en','eliminado_por'])

    def reactivar(self):
        self.es_activo = True
        self.eliminado_en = None
        self.eliminado_por = ""
        self.save(update_fields=['es_activo','eliminado_en','eliminado_por'])

class ListaPrecio(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    porcentaje = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    activa = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    def __str__(self): return f"{self.nombre} ({self.porcentaje}%)"

class ItemListaPrecio(models.Model):
    lista = models.ForeignKey(ListaPrecio, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
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
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name='items_presupuesto')
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
    class Meta:
        ordering = ['-fecha_venta']
    def __str__(self): return f"{self.codigo} - {self.cliente.nombre}"

class ItemVenta(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name='items_venta')
    cantidad = models.IntegerField(default=1)
    precio = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    def __str__(self): return f"{self.venta.codigo} - {self.producto.codigo} x{self.cantidad}"

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

# === NUEVO: AUDITORIA BLINDADA ===
class AuditoriaAccion(models.Model):
    TIPO_ACCION = [
        ('DESACTIVAR_PRODUCTO', 'Desactivar Producto'),
        ('REACTIVAR_PRODUCTO', 'Reactivar Producto'),
        ('INTENTO_BORRAR_BLOQUEADO', 'Intento Bloqueado Borrar Producto con Ventas'),
        ('LIMPIAR_DUPLICADOS', 'Limpiar Duplicados'),
        ('CREAR_VENTA', 'Crear Venta'),
        ('ELIMINAR_VENTA', 'Eliminar Venta'),
        ('OTRO', 'Otro'),
    ]
    fecha = models.DateTimeField(auto_now_add=True, db_index=True)
    usuario = models.CharField(max_length=150, default="sistema")
    accion = models.CharField(max_length=30, choices=TIPO_ACCION)
    modelo = models.CharField(max_length=50)
    objeto_id = models.CharField(max_length=50)
    detalle = models.TextField(blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-fecha']
        verbose_name_plural = "Auditorias"

    def __str__(self):
        return f"{self.fecha.strftime('%d/%m %H:%M')} - {self.accion} - {self.detalle[:60]}"

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
    version = models.CharField(max_length=20, default="2.1 BLINDADO")
    def __str__(self):
        return f"Config v{self.version} - {'BLOQUEADO' if self.bloqueado_global else 'OK'}"
