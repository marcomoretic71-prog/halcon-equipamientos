from django.contrib import admin
from.models import Cliente, Producto, Presupuesto, ItemPresupuesto, ListaPrecio, ItemListaPrecio, Venta

class ItemInline(admin.TabularInline):
    model = ItemPresupuesto
    extra = 0

class ItemListaInline(admin.TabularInline):
    model = ItemListaPrecio
    extra = 0

@admin.register(Presupuesto)
class PresupuestoAdmin(admin.ModelAdmin):
    list_display = ['codigo','cliente','creado','total'] # <-- era 'fecha', ahora 'creado'
    list_filter = ['creado']
    search_fields = ['codigo','cliente__nombre']
    inlines = [ItemInline]

@admin.register(ListaPrecio)
class ListaPrecioAdmin(admin.ModelAdmin):
    list_display = ['nombre','porcentaje','activa','creado']
    inlines = [ItemListaInline]

@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ['codigo','cliente','forma_pago','total','fecha_venta']
    list_filter = ['forma_pago','fecha_venta']
    search_fields = ['codigo','cliente__nombre']

admin.site.register(Cliente)
admin.site.register(Producto)