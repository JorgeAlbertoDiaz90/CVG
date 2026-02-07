from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from . import utils
from django.db import connection
# Create your views here.


# --------- CATALOGO DE PRODUCTOS -------

@login_required
def catalogo_productos(request):

    with connection.cursor() as cursor:
        cursor.execute(
            "CALL l_catalogos_productos()"
        )
        productos = utils.dictfetchall(cursor)
    
    return render(request,'catalogo_productos.html', {
        'productos': productos
    })


# ----------CATALOGO DE LINEAS-----------

@login_required
def catalogo_lineas(request):

    with connection.cursor() as cursor:
        cursor.execute(
            "CALL l_catalogos_lineas()"
        )
        lineas = utils.dictfetchall(cursor)
    
    return render(request,'catalogo_lineas.html', {
        'lineas': lineas
    })

# ------------CATALOGO DE SUCURSALES--------

@login_required
def catalogo_sucursales(request):

    with connection.cursor() as cursor:
        cursor.execute(
            "CALL l_catalogos_sucursales()"
        )
        sucursales = utils.dictfetchall(cursor)
    
    return render(request,'catalogo_sucursales.html', {
        'sucursales': sucursales
    })


# -------------CATALOGO DE PROVEEDORES-------

@login_required
def catalogo_grupos(request):

    with connection.cursor() as cursor:
        cursor.execute(
            "CALL l_catalogos_grupos()"
        )
        grupos = utils.dictfetchall(cursor)
    
    return render(request,'catalogo_grupos.html', {
        'grupos': grupos
    })

#---------------CATALOGO DE CLIENTES--------

@login_required
def catalogo_clientes(request):
    is_staff = request.user.is_staff
    idvend = request.user.idvend

    with connection.cursor() as cursor:
        cursor.execute(
            "CALL l_clientes(%s, %s)",[is_staff, idvend]
        )
        clientes = utils.dictfetchall(cursor)
    
    return render(request,'catalogo_clientes.html', {
        'clientes': clientes
    })


