from django.db import models

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
    class Meta:
        ordering = ['-fecha_venta']
    def __str__(self): return f"{self.codigo} - {self.cliente.nombre}"

class ItemVenta(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='items_venta')
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
