from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta, datetime
import json, uuid, os
from django.conf import settings
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from .models import Cliente, Producto, Presupuesto, ItemPresupuesto, ListaPrecio, ItemListaPrecio, Venta, ItemVenta, MovimientoCaja

DATOS_EMPRESA = {
    "whatsapp": "2983512672 / 3843400199",
    "direccion": "Ruta 89 Km. Quimili, SGO",
    "instagram": "halcon_equipamientos",
    "validez": "15 días",
    "seña": "10%",
    "alias": "halconequipamientos",
    "condiciones": "Se reserva con seña del 10%. Validez 15 días.",
    "footer": "¡Gracias por confiar en HALCÓN EQUIPAMIENTOS!"
}

def dashboard(request):
    hoy = timezone.now()
    hace_30 = hoy - timedelta(days=30)
    ventas_qs = Venta.objects.select_related('cliente').order_by('-fecha_venta')
    ventas_recientes = ventas_qs[:15]
    presupuestos = Presupuesto.objects.select_related('cliente').order_by('-creado')[:10]
    total_acum = ventas_qs.aggregate(Sum('total'))['total__sum'] or 0
    total_mes = ventas_qs.filter(fecha_venta__gte=hace_30).aggregate(Sum('total'))['total__sum'] or 0
    count_mes = ventas_qs.filter(fecha_venta__gte=hace_30).count()
    count_total = ventas_qs.count()
    if count_total == 0:
        total_acum = Presupuesto.objects.aggregate(Sum('total'))['total__sum'] or 0
        total_mes = Presupuesto.objects.filter(creado__gte=hace_30).aggregate(Sum('total'))['total__sum'] or 0
        count_mes = Presupuesto.objects.filter(creado__gte=hace_30).count()
        count_total = Presupuesto.objects.count()
    ticket_prom = total_acum / count_total if count_total else 0
    top_productos = ItemPresupuesto.objects.values('producto__codigo','producto__nombre').annotate(veces=Count('id')).order_by('-veces')[:5]
    stock_bajo = Producto.objects.filter(stock__lte=3).order_by('stock')[:10]
    clientes_nuevos = Cliente.objects.order_by('-creado')[:5]
    categorias = Producto.objects.values_list('categoria', flat=True).distinct().order_by('categoria')
    ingresos_mes = MovimientoCaja.objects.filter(tipo='INGRESO', fecha__gte=hace_30).aggregate(Sum('monto'))['monto__sum'] or 0
    egresos_mes = MovimientoCaja.objects.filter(tipo='EGRESO', fecha__gte=hace_30).aggregate(Sum('monto'))['monto__sum'] or 0
    total_ingresos = MovimientoCaja.objects.filter(tipo='INGRESO').aggregate(Sum('monto'))['monto__sum'] or 0
    total_egresos = MovimientoCaja.objects.filter(tipo='EGRESO').aggregate(Sum('monto'))['monto__sum'] or 0
    saldo_caja = total_ingresos - total_egresos
    movimientos_caja = MovimientoCaja.objects.order_by('-fecha')[:10]
    return render(request, 'dashboard.html', {
        'total_acum': total_acum, 'total_mes': total_mes, 'count_mes': count_mes,
        'count_total': count_total, 'ticket_prom': ticket_prom,
        'presupuestos': presupuestos, 'ventas_recientes': ventas_recientes,
        'top_productos': top_productos, 'stock_bajo': stock_bajo,
        'clientes_nuevos': clientes_nuevos, 'categorias': categorias, 'datos': DATOS_EMPRESA,
        'ingresos_mes': ingresos_mes, 'egresos_mes': egresos_mes,
        'saldo_caja': saldo_caja, 'movimientos_caja': movimientos_caja
    })

def caja_view(request):
    mes_param = request.GET.get('mes','')
    tipo_param = request.GET.get('tipo','')
    movimientos = MovimientoCaja.objects.all().order_by('-fecha')
    if tipo_param in ['INGRESO','EGRESO']:
        movimientos = movimientos.filter(tipo=tipo_param)
    if mes_param:
        try:
            year, month = map(int, mes_param.split('-'))
            movimientos = movimientos.filter(fecha__year=year, fecha__month=month)
        except:
            mes_param = ""
    ingresos_filtrados = movimientos.filter(tipo='INGRESO').aggregate(Sum('monto'))['monto__sum'] or 0
    egresos_filtrados = movimientos.filter(tipo='EGRESO').aggregate(Sum('monto'))['monto__sum'] or 0
    balance_filtrado = ingresos_filtrados - egresos_filtrados
    count_ingresos = movimientos.filter(tipo='INGRESO').count()
    count_egresos = movimientos.filter(tipo='EGRESO').count()
    total_ing = MovimientoCaja.objects.filter(tipo='INGRESO').aggregate(Sum('monto'))['monto__sum'] or 0
    total_egr = MovimientoCaja.objects.filter(tipo='EGRESO').aggregate(Sum('monto'))['monto__sum'] or 0
    saldo_actual = total_ing - total_egr
    movimientos_list = list(movimientos.select_related('venta')[:200])
    movimientos_rev = list(reversed(movimientos_list))
    temp = 0
    acum_map = {}
    for m in movimientos_rev:
        if m.tipo == 'INGRESO':
            temp += float(m.monto)
        else:
            temp -= float(m.monto)
        acum_map[m.id] = temp
    for m in movimientos_list:
        m.saldo_acum = acum_map.get(m.id, 0)
    meses_qs = MovimientoCaja.objects.dates('fecha','month',order='DESC')
    meses_disponibles = [{'value': d.strftime('%Y-%m'), 'label': d.strftime('%m/%Y')} for d in meses_qs]
    if mes_param:
        try:
            y,m = map(int, mes_param.split('-'))
            mes_label = datetime(y,m,1).strftime('%m/%Y')
        except:
            mes_label = "Filtrado"
    else:
        mes_label = "Mes Actual" if not tipo_param else tipo_param
    return render(request, 'caja.html', {
        'movimientos': movimientos_list,
        'saldo_actual': saldo_actual,
        'ingresos_filtrados': ingresos_filtrados,
        'egresos_filtrados': egresos_filtrados,
        'balance_filtrado': balance_filtrado,
        'count_ingresos': count_ingresos,
        'count_egresos': count_egresos,
        'mes_label': mes_label,
        'meses_disponibles': meses_disponibles,
        'mes_seleccionado': mes_param,
        'tipo_seleccionado': tipo_param,
    })

@csrf_exempt
def api_caja_eliminar(request):
    if request.method == 'POST':
        try:
            d = json.loads(request.body)
            mid = d.get('id')
            MovimientoCaja.objects.filter(id=mid).delete()
            return JsonResponse({'ok': True})
        except Exception as e:
            return JsonResponse({'ok': False, 'error': str(e)})
    return JsonResponse({'ok': False})

def productos_view(request):
    categorias = Producto.objects.values_list('categoria', flat=True).distinct().order_by('categoria')
    return render(request, 'productos.html', {'categorias': categorias, 'count_productos': Producto.objects.count(), 'datos': DATOS_EMPRESA})

def listas_view(request):
    listas = ListaPrecio.objects.prefetch_related('items__producto').all().order_by('nombre')
    return render(request, 'listas.html', {'listas': listas, 'datos': DATOS_EMPRESA})

def presupuestos_view(request):
    presupuestos = Presupuesto.objects.select_related('cliente').prefetch_related('items__producto').order_by('-creado')[:100]
    productos = Producto.objects.all().order_by('codigo')
    clientes = Cliente.objects.all().order_by('-creado')[:100]
    listas = ListaPrecio.objects.all()
    total_acum = Presupuesto.objects.aggregate(Sum('total'))['total__sum'] or 0
    return render(request, 'lista.html', {
        'presupuestos': presupuestos, 'productos': productos,
        'clientes': clientes, 'listas': listas,
        'total_acumulado': total_acum, 'count': presupuestos.count(),
        'datos': DATOS_EMPRESA
    })

def ventas_view(request):
    ventas = Venta.objects.select_related('cliente','presupuesto').order_by('-fecha_venta')[:200]
    total_ventas = Venta.objects.aggregate(Sum('total'))['total__sum'] or 0
    ventas_hoy = Venta.objects.filter(fecha_venta__date=timezone.now().date()).aggregate(Sum('total'))['total__sum'] or 0
    count_ventas = Venta.objects.count()
    ticket_promedio = total_ventas / count_ventas if count_ventas else 0
    presupuestos = Presupuesto.objects.select_related('cliente').order_by('-creado')[:20]
    total_efectivo = Venta.objects.filter(forma_pago='EFECTIVO').aggregate(Sum('total'))['total__sum'] or 0
    total_transfer = Venta.objects.filter(forma_pago='TRANSFERENCIA').aggregate(Sum('total'))['total__sum'] or 0
    total_tarjeta = total_ventas - total_efectivo - total_transfer
    return render(request, 'ventas.html', {
        'ventas': ventas, 'total_ventas': total_ventas, 'ventas_hoy': ventas_hoy,
        'count_ventas': count_ventas, 'ticket_promedio': ticket_promedio,
        'total_efectivo': total_efectivo, 'total_transfer': total_transfer,
        'total_tarjeta': total_tarjeta, 'presupuestos': presupuestos, 'datos': DATOS_EMPRESA
    })

def api_buscar_productos(request):
    q = request.GET.get('q','').strip()
    cat = request.GET.get('cat','TODOS').strip().upper()
    try:
        productos = Producto.objects.all()
        if cat != 'TODOS':
            productos = productos.filter(categoria__iexact=cat)
        if q:
            field_names = [f.name for f in Producto._meta.get_fields() if hasattr(f, 'name')]
            query = Q(codigo__icontains=q) | Q(nombre__icontains=q)
            if 'barcode' in field_names:
                query |= Q(barcode__icontains=q)
            if 'compatibilidad' in field_names:
                query |= Q(compatibilidad__icontains=q)
            if 'compat' in field_names:
                query |= Q(compat__icontains=q)
            productos = productos.filter(query)
        productos = productos.order_by('codigo')[:100]
        data = []
        for p in productos:
            compat_val = ""
            try:
                if hasattr(p, 'compatibilidad') and p.compatibilidad:
                    compat_val = p.compatibilidad
                elif hasattr(p, 'compat') and hasattr(p.compat, '__str__') and p.compat:
                    compat_val = str(p.compat)
                else:
                    compat_val = p.nombre
            except:
                compat_val = p.nombre
            data.append({
                'id': p.id,
                'codigo': p.codigo,
                'barcode': getattr(p, 'barcode', '') or '',
                'nombre': p.nombre,
                'precio': float(p.precio) if p.precio else 0,
                'stock': p.stock,
                'categoria': getattr(p, 'categoria', 'OTRO') or 'OTRO',
                'compat': compat_val,
            })
        return JsonResponse(data, safe=False)
    except Exception as e:
        print(f"ERROR api_buscar_productos q={q}: {e}")
        return JsonResponse([], safe=False)

@csrf_exempt
def api_guardar_producto(request):
    if request.method == 'POST':
        try:
            d = json.loads(request.body)
            prod_id = d.get('id')
            p = Producto.objects.get(id=prod_id) if prod_id else Producto()
            p.codigo = d['codigo'].strip()
            p.barcode = d.get('barcode','').strip() or None
            p.nombre = d['nombre'].strip()
            p.categoria = d.get('categoria','OTRO')
            p.precio = float(d.get('precio',0))
            p.stock = int(d.get('stock',0))
            fields = [f.name for f in Producto._meta.get_fields() if hasattr(f, 'name')]
            if 'compatibilidad' in fields:
                p.compatibilidad = d.get('compat','') or d.get('compatibilidad','')
            if 'compat' in fields:
                p.compat = d.get('compat','') or d.get('compatibilidad','')
            p.save()
            return JsonResponse({'ok': True, 'id': p.id})
        except Exception as e:
            return JsonResponse({'ok': False, 'error': str(e)})
    return JsonResponse({'ok': False})

@csrf_exempt
def crear_presupuesto(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        cliente, _ = Cliente.objects.get_or_create(nombre=data['cliente_nombre'].strip(), defaults={'telefono': data.get('telefono','')})
        if data.get('telefono'):
            cliente.telefono = data.get('telefono')
            cliente.save()
        codigo = f"HAL-{uuid.uuid4().hex[:4].upper()}"
        pres = Presupuesto.objects.create(codigo=codigo, cliente=cliente, vehiculo=data.get('vehiculo',''), colocacion=data.get('colocacion',0), subtotal=data.get('subtotal',0), total=data.get('total',0))
        for it in data.get('items',[]):
            prod = Producto.objects.get(id=it['id'])
            precio_item = it.get('precio', it.get('precio_unitario', prod.precio))
            try:
                ItemPresupuesto.objects.create(presupuesto=pres, producto=prod, cantidad=it['cantidad'], precio=precio_item, precio_unitario=precio_item)
            except TypeError:
                try:
                    ItemPresupuesto.objects.create(presupuesto=pres, producto=prod, cantidad=it['cantidad'], precio=precio_item)
                except:
                    ItemPresupuesto.objects.create(presupuesto=pres, producto=prod, cantidad=it['cantidad'], precio_unitario=precio_item)
        return JsonResponse({'ok': True, 'codigo': codigo})
    return JsonResponse({'ok': False})

@csrf_exempt
def modificar_lista(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        lista = ListaPrecio.objects.get(id=data['lista_id'])
        porcentaje = float(data['porcentaje'])
        if porcentaje == 0: return JsonResponse({'ok': False, 'error': 'Porcentaje 0'})
        factor = 1 + (porcentaje/100)
        for item in lista.items.select_related('producto').all():
            precio_base = 0
            try: precio_base = float(item.precio) if float(item.precio) > 0 else 0
            except: pass
            if precio_base <= 0:
                try: precio_base = float(item.precio_unitario) if hasattr(item, 'precio_unitario') else 0
                except: precio_base = 0
            if precio_base <= 0: precio_base = float(item.producto.precio)
            if precio_base <= 0: continue
            nuevo = round(precio_base * factor, 2)
            try: item.precio = nuevo
            except: pass
            try:
                if hasattr(item, 'precio_unitario'): item.precio_unitario = nuevo
            except: pass
            item.save()
            item.producto.precio = nuevo
            item.producto.save()
        return JsonResponse({'ok': True})
    return JsonResponse({'ok': False})

@csrf_exempt
def editar_precio_item_lista(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            item_id = data.get('item_id')
            precio_raw = data.get('precio')
            if precio_raw is None or str(precio_raw).strip() == "": return JsonResponse({'ok': False, 'error': 'precio vacío'})
            nuevo = float(precio_raw)
            if nuevo <= 0: return JsonResponse({'ok': False, 'error': 'precio debe ser > 0'})
            item = ItemListaPrecio.objects.select_related('producto').get(id=item_id)
            try: item.precio = nuevo
            except: pass
            if hasattr(item, 'precio_unitario'): item.precio_unitario = nuevo
            item.save()
            item.producto.precio = nuevo
            item.producto.save()
            return JsonResponse({'ok': True, 'nuevo_precio': nuevo})
        except Exception as e:
            return JsonResponse({'ok': False, 'error': str(e)})
    return JsonResponse({'ok': False})

@csrf_exempt
def api_sumar_stock(request):
    if request.method == 'POST':
        d=json.loads(request.body)
        p=Producto.objects.get(id=d['id'])
        p.stock += int(d['cantidad'])
        p.save()
        return JsonResponse({'ok':True, 'nuevo_stock': p.stock})
    return JsonResponse({'ok':False})

@csrf_exempt
def api_reponer_codigo(request):
    if request.method == 'POST':
        d=json.loads(request.body)
        try:
            p=Producto.objects.filter(Q(codigo__iexact=d['codigo'].strip()) | Q(barcode__iexact=d['codigo'].strip())).first()
            if not p: raise Exception('no encontrado')
            p.stock += int(d['cantidad'])
            p.save()
            return JsonResponse({'ok':True})
        except:
            return JsonResponse({'ok':False, 'error':'Código no encontrado'})
    return JsonResponse({'ok':False})

@csrf_exempt
def api_convertir_a_venta(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        codigo_pres = data.get('codigo_presupuesto')
        forma_pago = data.get('forma_pago','EFECTIVO')
        try:
            pres = Presupuesto.objects.select_related('cliente').prefetch_related('items__producto').get(codigo=codigo_pres)
            if hasattr(pres, 'venta') and pres.venta is not None:
                return JsonResponse({'ok': False, 'error': 'Este presupuesto ya es una venta'})
            codigo_venta = f"VEN-{uuid.uuid4().hex[:4].upper()}"
            venta = Venta.objects.create(codigo=codigo_venta, presupuesto=pres, cliente=pres.cliente, vehiculo=pres.vehiculo, total=pres.total, forma_pago=forma_pago)
            for item in pres.items.all():
                prod = item.producto
                prod.stock = max(0, prod.stock - item.cantidad)
                prod.save()
            venta.stock_descontado = True
            venta.save()
            MovimientoCaja.objects.create(tipo='INGRESO', concepto=f"Venta {codigo_venta} - {pres.cliente.nombre}", monto=venta.total, forma_pago=forma_pago, venta=venta)
            return JsonResponse({'ok': True, 'codigo_venta': codigo_venta})
        except Presupuesto.DoesNotExist:
            return JsonResponse({'ok': False, 'error': 'Presupuesto no encontrado'})
        except Exception as e:
            return JsonResponse({'ok': False, 'error': str(e)})
    return JsonResponse({'ok': False})

@csrf_exempt
def api_venta_directa(request):
    if request.method!= 'POST':
        return JsonResponse({'ok': False})
    try:
        data = json.loads(request.body)
        cliente_nombre = data.get('cliente_nombre','').strip()
        if not cliente_nombre:
            return JsonResponse({'ok': False, 'error': 'Falta cliente'})
        cliente, _ = Cliente.objects.get_or_create(nombre=cliente_nombre, defaults={'telefono': data.get('telefono',''), 'vehiculo_anio': data.get('vehiculo','')})
        codigo = f"VEN-{uuid.uuid4().hex[:4].upper()}"
        venta = Venta.objects.create(codigo=codigo, cliente=cliente, vehiculo=data.get('vehiculo',''), total=data.get('total',0), forma_pago=data.get('forma_pago','EFECTIVO'), es_directa=True, stock_descontado=True)
        for it in data.get('items',[]):
            prod = Producto.objects.get(id=it['id'])
            ItemVenta.objects.create(venta=venta, producto=prod, cantidad=int(it['cantidad']), precio=float(it.get('precio', prod.precio)))
            prod.stock = max(0, prod.stock - int(it['cantidad']))
            prod.save()
        MovimientoCaja.objects.create(tipo='INGRESO', concepto=f"Venta Directa {codigo} - {cliente.nombre}", monto=venta.total, forma_pago=venta.forma_pago, venta=venta)
        return JsonResponse({'ok': True, 'codigo': codigo})
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)})

@csrf_exempt
def api_caja_movimiento(request):
    if request.method == 'POST':
        try:
            d = json.loads(request.body)
            MovimientoCaja.objects.create(tipo=d['tipo'], concepto=d['concepto'], monto=float(d['monto']), forma_pago=d.get('forma_pago','EFECTIVO'), nota=d.get('nota',''))
            return JsonResponse({'ok': True})
        except Exception as e:
            return JsonResponse({'ok': False, 'error': str(e)})
    return JsonResponse({'ok': False})

def api_caja_lista(request):
    movs = MovimientoCaja.objects.order_by('-fecha')[:100]
    data = [{'id': m.id, 'fecha': m.fecha.strftime('%d/%m %H:%M'), 'tipo': m.tipo, 'concepto': m.concepto, 'monto': float(m.monto), 'forma_pago': m.forma_pago} for m in movs]
    return JsonResponse(data, safe=False)

def pdf_presupuesto(request, codigo):
    pres = Presupuesto.objects.select_related('cliente').prefetch_related('items__producto').get(codigo=codigo)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{codigo}.pdf"'
    p = canvas.Canvas(response, pagesize=A4)
    w, h = A4
    d = DATOS_EMPRESA
    p.setFillColorRGB(0.08,0.08,0.08)
    p.rect(0, h-120, w, 120, fill=1, stroke=0)
    try:
        logo_path = os.path.join(settings.BASE_DIR, 'equipamientos', 'static', 'logo_halcon_circular.png')
        if os.path.exists(logo_path):
            p.drawImage(ImageReader(logo_path), 35, h-95, width=65, height=65, mask='auto')
    except: pass
    p.setFillColorRGB(1,1,1)
    p.setFont("Helvetica-Bold", 16)
    p.drawString(115, h-38, "HALCÓN EQUIPAMIENTOS")
    p.setFont("Helvetica", 9)
    p.setFillColorRGB(0.9,0.9,0.9)
    p.drawString(115, h-52, f"{d['direccion']}")
    p.drawString(115, h-64, f"WhatsApp: {d['whatsapp']}")
    p.drawString(115, h-76, f"Instagram: @{d['instagram']}")
    p.setFillColorRGB(1,0.84,0)
    p.setFont("Helvetica-Bold", 11)
    p.drawRightString(w-35, h-40, "PRESUPUESTO")
    p.setFillColorRGB(1,1,1)
    p.setFont("Helvetica-Bold", 15)
    p.drawRightString(w-35, h-56, f"{pres.codigo}")
    p.setFont("Helvetica", 9)
    p.setFillColorRGB(0.8,0.8,0.8)
    p.drawRightString(w-35, h-70, f"{pres.creado.strftime('%d/%m/%Y')} - Validez {d['validez']}")
    p.setFillColorRGB(0.13,0.13,0.13)
    p.roundRect(40, h-185, w-80, 55, 10, fill=1, stroke=0)
    p.setFillColorRGB(1,0.55,0)
    p.rect(40, h-185, 4, 55, fill=1, stroke=0)
    p.setFillColorRGB(1,1,1)
    p.setFont("Helvetica-Bold", 11)
    p.drawString(60, h-160, f"CLIENTE: {pres.cliente.nombre.upper()}")
    p.setFont("Helvetica", 9.5)
    p.drawString(60, h-175, f"Tel: {pres.cliente.telefono} | Vehículo: {pres.vehiculo}")
    y = h-225
    p.setFillColorRGB(1,0.84,0)
    p.rect(40, y-6, w-80, 22, fill=1, stroke=0)
    p.setFillColorRGB(0,0,0)
    p.setFont("Helvetica-Bold", 9)
    p.drawString(45, y+2, "CODIGO")
    p.drawString(120, y+2, "PRODUCTO")
    p.drawString(380, y+2, "CANT")
    p.drawString(420, y+2, "P.UNIT")
    p.drawString(490, y+2, "SUBTOTAL")
    y -= 25
    for idx, it in enumerate(pres.items.all()):
        if y < 150:
            p.showPage()
            y = h-50
        if idx % 2 == 0:
            p.setFillColorRGB(0.96,0.96,0.96)
            p.rect(40, y-4, w-80, 16, fill=1, stroke=0)
        p.setFillColorRGB(0,0,0)
        p.setFont("Helvetica", 9)
        nombre = it.producto.nombre[:52]
        precio_u = getattr(it, 'precio_unitario', None) or getattr(it, 'precio', 0)
        p.drawString(45, y, it.producto.codigo[:14])
        p.drawString(120, y, nombre)
        p.drawCentredString(390, y, str(it.cantidad))
        p.drawRightString(460, y, f"${float(precio_u):,.0f}")
        p.drawRightString(560, y, f"${float(it.cantidad*precio_u):,.0f}")
        y -= 16
    y -= 12
    p.setStrokeColorRGB(0.8,0.8,0.8)
    p.line(340, y, w-40, y)
    y -= 18
    p.setFont("Helvetica", 10)
    p.setFillColorRGB(0,0,0)
    p.drawRightString(460, y, "Subtotal:")
    p.drawRightString(560, y, f"${float(pres.subtotal):,.0f}")
    y -= 16
    p.drawRightString(460, y, "Colocación:")
    p.drawRightString(560, y, f"${float(pres.colocacion):,.0f}")
    y -= 26
    p.setFillColorRGB(1,0.84,0)
    p.roundRect(360, y-8, 200, 30, 8, fill=1, stroke=0)
    p.setFillColorRGB(0,0,0)
    p.setFont("Helvetica-Bold", 12)
    p.drawRightString(550, y, f"TOTAL: ${float(pres.total):,.0f}")
    y -= 45
    p.setFont("Helvetica-Bold", 9)
    p.setFillColorRGB(0,0,0)
    p.drawString(40, y, f"Condiciones: {d['condiciones']}")
    y -= 14
    p.setFont("Helvetica", 8.5)
    p.setFillColorRGB(0.3,0.3,0.3)
    p.drawString(40, y, f"Alias: {d['alias']} | {d['direccion']}")
    p.setFont("Helvetica-Bold", 8)
    p.setFillColorRGB(0.5,0.5,0.5)
    p.drawCentredString(w/2, 40, d['footer'])
    p.showPage()
    p.save()
    return response

from django.db import transaction
import re

@csrf_exempt
def api_crear_lista(request):
    if request.method == 'POST':
        try:
            d = json.loads(request.body)
            nombre = d.get('nombre','').strip()
            if not nombre:
                return JsonResponse({'ok': False, 'error': 'Nombre vacío'})
            if ListaPrecio.objects.filter(nombre__iexact=nombre).exists():
                return JsonResponse({'ok': False, 'error': f'Ya existe una lista llamada {nombre}'})
            lista = ListaPrecio.objects.create(nombre=nombre, porcentaje=0, activa=True)
            return JsonResponse({'ok': True, 'id': lista.id, 'nombre': lista.nombre})
        except Exception as e:
            return JsonResponse({'ok': False, 'error': str(e)})
    return JsonResponse({'ok': False, 'error': 'Método no permitido'})

def _limpiar_precio_br(valor):
    if valor is None:
        return 0
    s = str(valor).strip()
    if not s:
        return 0
    s = s.replace('$','').replace(' ','').strip()
    if ',' in s and '.' in s:
        s = s.replace('.','').replace(',','.')
    elif ',' in s:
        s = s.replace(',','.')
    try:
        m = re.findall(r'[\d\.]+', s)
        return float(m[0]) if m else 0
    except:
        return 0

@csrf_exempt
@transaction.atomic
def api_importar_lista_excel(request):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'POST requerido'})
    try:
        data = json.loads(request.body)
        lista_id = data.get('lista_id','nueva')
        nombre_nueva = data.get('nombre_nueva','').strip()
        items = data.get('items', [])
        if not items:
            return JsonResponse({'ok': False, 'error': 'No se recibieron items'})
        if lista_id == 'nueva':
            if not nombre_nueva:
                from datetime import datetime
                nombre_nueva = f"BRACCO - {datetime.now().strftime('%d-%m-%Y')}"
            lista, _ = ListaPrecio.objects.get_or_create(nombre=nombre_nueva, defaults={'porcentaje':0})
        else:
            lista = ListaPrecio.objects.get(id=lista_id)
            if nombre_nueva and nombre_nueva != lista.nombre:
                lista.nombre = nombre_nueva
                lista.save()
        creados = 0
        actualizados = 0
        for row in items:
            codigo = str(row.get('codigo','')).strip().upper()
            nombre_prod = str(row.get('nombre','')).strip()
            if not codigo:
                continue
            precio = _limpiar_precio_br(row.get('precio',0))
            if precio <= 0:
                continue
            if not nombre_prod:
                nombre_prod = codigo
            prod, is_new = Producto.objects.get_or_create(
                codigo=codigo,
                defaults={'nombre': nombre_prod, 'categoria': 'BRACCO', 'precio': precio, 'stock': 0}
            )
            if is_new:
                creados += 1
            else:
                prod.nombre = nombre_prod
                prod.precio = precio
                if not prod.categoria or prod.categoria == 'OTRO':
                    prod.categoria = 'BRACCO'
                prod.save()
                actualizados += 1
            item, item_new = ItemListaPrecio.objects.get_or_create(
                lista=lista,
                producto=prod,
                defaults={'precio': precio, 'precio_unitario': precio}
            )
            if not item_new:
                item.precio = precio
                item.precio_unitario = precio
                item.save()
        return JsonResponse({
            'ok': True,
            'creados': creados,
            'actualizados': actualizados,
            'lista_nombre': lista.nombre,
            'lista_id': lista.id,
            'total_lista': lista.items.count()
        })
    except ListaPrecio.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Lista no encontrada'})
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)})

def api_exportar_lista_excel(request):
    import csv
    lista_id = request.GET.get('lista_id')
    try:
        lista = ListaPrecio.objects.get(id=lista_id)
        response = HttpResponse(content_type='text/csv; charset=latin1')
        response['Content-Disposition'] = f'attachment; filename="{lista.nombre}.csv"'
        response.write(u'\ufeff'.encode('utf8'))
        writer = csv.writer(response, delimiter=';', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(['CODIGO', 'NOMBRE', 'PRECIO'])
        for item in lista.items.select_related('producto').all().order_by('producto__codigo'):
            precio_str = str(item.precio).replace('.', ',')
            writer.writerow([item.producto.codigo, item.producto.nombre, precio_str])
        return response
    except Exception as e:
        return HttpResponse(f"Error: {e}", status=400)


@csrf_exempt
def api_cambiar_password(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            new_pass = data.get('new_password','').strip()
            if len(new_pass) < 6:
                return JsonResponse({'ok': False, 'error': 'Mínimo 6 caracteres'})
            if not request.user.is_authenticated:
                return JsonResponse({'ok': False, 'error': 'No autenticado'})
            request.user.set_password(new_pass)
            request.user.save()
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, request.user)
            return JsonResponse({'ok': True})
        except Exception as e:
            return JsonResponse({'ok': False, 'error': str(e)})
    return JsonResponse({'ok': False, 'error': 'Método no permitido'})
