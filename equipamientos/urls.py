from django.urls import path
from . import views
from . import views_super

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('productos/', views.productos_view, name='productos'),
    path('listas/', views.listas_view, name='listas'),
    path('presupuestos/', views.presupuestos_view, name='presupuestos'),
    
    # APIs PRODUCTOS
    path('api/buscar_productos/', views.api_buscar_productos, name='api_buscar_productos'),
    path('api/guardar_producto/', views.api_guardar_producto, name='api_guardar_producto'),
    path('api/eliminar_producto/<int:producto_id>/', views.api_eliminar_producto, name='api_eliminar_producto'),
    path('api/limpiar_duplicados_global/', views.api_limpiar_duplicados_global, name='api_limpiar_duplicados_global'),
    path('api/actualizar_stock/', views.api_actualizar_stock, name='api_actualizar_stock'),

    # PRESUPUESTOS
    path('crear_presupuesto/', views.crear_presupuesto, name='crear_presupuesto'),
    path('modificar_lista/', views.modificar_lista, name='modificar_lista'),
    path('editar_precio_item_lista/', views.editar_precio_item_lista, name='editar_precio_item_lista'),
    
    # PDF
    path('pdf/<str:codigo>/', views.pdf_presupuesto, name='pdf_presupuesto'),
    path('presupuesto/pdf/<str:codigo>/', views.pdf_presupuesto, name='pdf_presupuesto_alt'),
    path('presupuesto/nuevo/', views.presupuestos_view, name='presupuesto_nuevo'),

    path('api/stock/sumar/', views.api_sumar_stock, name='api_sumar_stock'),
    path('api/stock/reponer_codigo/', views.api_reponer_codigo, name='api_reponer_codigo'),

    path('ventas/', views.ventas_view, name='ventas'),
    path('api/convertir_a_venta/', views.api_convertir_a_venta, name='convertir_venta'),
    path('api/venta_directa/', views.api_venta_directa, name='venta_directa'),
    path('api/caja_movimiento/', views.api_caja_movimiento, name='api_caja_movimiento'),
    path('api/caja_lista/', views.api_caja_lista, name='api_caja_lista'),
    path('caja/', views.caja_view, name='caja'),
    path('api/caja_eliminar/', views.api_caja_eliminar, name='api_caja_eliminar'),

    # LISTAS
    path('api/crear_lista/', views.api_crear_lista, name='api_crear_lista'),
    path('api/importar_lista_excel/', views.api_importar_lista_excel, name='api_importar_lista_excel'),
    path('api/exportar_lista_excel/', views.api_exportar_lista_excel, name='api_exportar_lista_excel'),
    path('api/eliminar_item_lista/', views.api_eliminar_item_lista, name='api_eliminar_item_lista'),
    path('api/limpiar_duplicados_lista/', views.api_limpiar_duplicados_lista, name='api_limpiar_duplicados_lista'),

    # LOGIN
    path('login/', views_super.login_view, name='login'),
    path('logout/', views_super.logout_view, name='logout'),
    path('super-admin/', views_super.super_admin_dashboard, name='super_admin'),
    path('api/super/bloquear/', views_super.api_bloquear_empresa, name='api_bloquear'),
    path('api/super/bloqueo-global/', views_super.api_bloqueo_global, name='api_bloqueo_global'),
    path('api/cambiar-password/', views.api_cambiar_password, name='cambiar_password'),
]
