from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
import json

def es_superadmin(user):
    return user.is_authenticated and (user.is_superuser or user.username in ['marcomoretic', 'marco_moretic', 'superadmin', 'halcon_admin', 'cliente'])

@csrf_exempt
def login_view(request):
    if request.user.is_authenticated:
        return redirect('/')
    
    if request.method == 'POST':
        try:
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST
            username = data.get('username')
            password = data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return JsonResponse({'ok': True})
            else:
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
    return render(request, 'super_admin.html', {'empresas': []})

@csrf_exempt
@login_required
@user_passes_test(es_superadmin)
def api_bloquear_empresa(request):
    return JsonResponse({'ok': False})

@csrf_exempt
@login_required
@user_passes_test(es_superadmin)
def api_bloqueo_global(request):
    return JsonResponse({'ok': False})