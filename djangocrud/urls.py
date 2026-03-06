from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime
import json

# 🔐 FUNCIÓN DE SEGURIDAD PARA ROSITA
def es_rosita(user):
    return user.is_authenticated and user.username == 'rosita'

# -----------------------------------------------------------
# 🌍 VISTAS DE PÁGINAS (RENDERIZADO)
# -----------------------------------------------------------

@login_required
def tipos(request):
    """ Página de Catálogo y Apartado para Profesores y Rosita """
    return render(request, 'tipos.html')

@user_passes_test(es_rosita)
def formulario(request):
    """ Página exclusiva de Rosita para registrar inventario nuevo """
    return render(request, 'formulario.html')

@login_required
def radar(request):
    """ Página de Inventario de Balones """
    return render(request, 'radar.html')

# -----------------------------------------------------------
# 🚀 APIS DE PROCESAMIENTO (PARA EVITAR ERROR 500)
# -----------------------------------------------------------

@login_required
def api_apartar_prenda(request):
    """ API que recibe el apartado de los profesores """
    if request.method == 'POST':
        try:
            # 1. Obtener datos del formulario
            profesor = request.POST.get('profesor')
            prenda = request.POST.get('prenda_nombre')
            fecha_uso_str = request.POST.get('fecha_uso')

            if not fecha_uso_str:
                return JsonResponse({'status': 'error', 'message': 'Falta la fecha'}, status=400)

            # 2. Validación en el servidor (Regla de 10 días)
            fecha_uso = datetime.strptime(fecha_uso_str, '%Y-%m-%d').date()
            hoy = timezone.now().date()
            diferencia = (fecha_uso - hoy).days

            if diferencia < 10:
                return JsonResponse({
                    'status': 'error', 
                    'message': 'No cumple los 10 días de anticipación.'
                }, status=400)

            # 3. Registro lógico (Aquí conectarás tu modelo más adelante)
            print(f"✅ REGISTRO EXITOSO: {profesor} reservó {prenda} para el {fecha_uso}")

            return JsonResponse({
                'status': 'ok', 
                'message': f'Reserva confirmada para {profesor}.'
            })

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

@user_passes_test(es_rosita)
def api_guardar_prenda(request):
    """ API para que Rosita registre ropa nueva """
    if request.method == 'POST':
        try:
            nombre = request.POST.get('nombre')
            categoria = request.POST.get('categoria')
            imagen = request.FILES.get('imagen') 

            # Simulación de guardado
            return JsonResponse({'status': 'ok', 'message': 'Prenda guardada correctamente'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
            
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def api_obtener_prendas(request):
    """ Envía las prendas al catálogo de tipos.html """
    data = [
        {"id": 1, "nombre": "Uniforme Titular Sub-15", "estado": "Disponible"},
        {"id": 2, "nombre": "Petos Naranja", "estado": "En préstamo"},
    ]
    return JsonResponse(data, safe=False)

# -----------------------------------------------------------
# ⚽ OTRAS VISTAS
# -----------------------------------------------------------

@login_required
def videos(request): return render(request, 'videos.html')

@login_required
def voz(request): return render(request, 'voz.html')

@login_required
def home(request): return render(request, 'home.html')

# Agrega aquí tus otras funciones de balones (api_guardar_entrega, etc.)