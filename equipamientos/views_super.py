from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db.models import Sum
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
import json

# Intentamos importar tus modelos extra, si no existen no se cae
try:
    from .models import EmpresaCliente, RegistroAcceso, ConfigSistema, Venta, MovimientoCaja, Presupuesto, Producto
    TIENE_MODELOS_EXTRA = True
except ImportError:
    from .models import Venta, MovimientoCaja, Presupuesto, Producto
    TIENE_MODELOS_EXTRA = False

def es_superadmin(user):
    return user.is_authenticated and (user.is_superuser or user.username in ['marcomoretic', 'marco_moretic', 'superadmin', 'halcon_admin'])

def login_view(request):
    if request.user.is_authenticated:
        if es_superadmin(request.user):
            return redirect('/super-admin/')
        return redirect('/')
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            username = data.get('username')
            password = data.get('password')
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                if TIENE_MODELOS_EXTRA:
                    try:
                        RegistroAcceso.objects.create(usuario=user.username, accion="LOGIN", ip=request.META.get('REMOTE_ADDR'))
                    except:
                        pass
                return JsonResponse({'ok': True, 'is_super': es_superadmin(user)})
            return JsonResponse({'ok': False, 'error': 'Usuario o contraseña incorrectos'})
        except Exception as e:
            return JsonResponse({'ok': False, 'error': str(e)})
            
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('/login/')

@login_required
@user_passes_test(es_superadmin)
def super_admin_dashboard(request):
    if not TIENE_MODELOS_EXTRA:
        return render(request, 'super_admin.html', {'empresas': [], 'accesos': []})
    
    empresas = EmpresaCliente.objects.all().order_by('-fecha_alta')
    config = ConfigSistema.objects.first()
    if not config:
        config = ConfigSistema.objects.create()
    total_ventas = Venta.objects.aggregate(Sum('total'))['total__sum'] or 0
    ventas_hoy = Venta.objects.filter(fecha_venta__date=timezone.now().date()).aggregate(Sum('total'))['total__sum'] or 0
    total_productos = Producto.objects.count()
    total_presupuestos = Presupuesto.objects.count()
    accesos = RegistroAcceso.objects.order_by('-fecha')[:20]
    total_ing = MovimientoCaja.objects.filter(tipo='INGRESO').aggregate(Sum('monto'))['monto__sum'] or 0
    total_egr = MovimientoCaja.objects.filter(tipo='EGRESO').aggregate(Sum('monto'))['monto__sum'] or 0
    saldo = total_ing - total_egr
    return render(request, 'super_admin.html', {
        'empresas': empresas, 'config': config,
        'total_ventas': total_ventas, 'ventas_hoy': ventas_hoy,
        'total_productos': total_productos, 'total_presupuestos': total_presupuestos,
        'accesos': accesos, 'saldo': saldo, 'total_ing': total_ing, 'total_egr': total_egr,
    })

@csrf_exempt
@login_required
@user_passes_test(es_superadmin)
def api_bloquear_empresa(request):
    return JsonResponse({'ok': False, 'error': 'Modelo no disponible'})

@csrf_exempt
@login_required
@user_passes_test(es_superadmin)
def api_bloqueo_global(request):
    return JsonResponse({'ok': False, 'error': 'Modelo no disponible'})

def check_sistema_bloqueado():
    return False, ""