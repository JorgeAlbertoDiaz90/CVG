from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from . import utils
from django.db import connection
from django.http import JsonResponse
# Create your views here.


# --------- CATALOGO DE PRODUCTOS -------

@login_required
def catalogo_productos(request):
    search = request.GET.get('search', '').strip()
    page = int(request.GET.get('page', 1))

    limit = 20
    offset = (page - 1) * limit

    with connection.cursor() as cursor:
        cursor.execute(
            "CALL l_catalogos_productos(%s, %s, %s)",
            [search, limit, offset]
        )

        # total
        total = utils.dictfetchall(cursor)[0]['total']

        # productos
        cursor.nextset()
        productos = utils.dictfetchall(cursor)

    total_pages = (total + limit - 1) // limit

    # Rango tipo Google
    rango = range(max(1, page - 2), min(total_pages + 1, page + 3))

    return render(request, 'catalogo_productos.html', {
        'productos': productos,
        'page': page,
        'total_pages': total_pages,
        'rango': rango,
        'search': search
    })

@login_required
def catalogo_productos_ajax(request):

    search = request.GET.get('search', '').strip()
    page = int(request.GET.get('page', 1))

    limit = 20
    offset = (page - 1) * limit

    with connection.cursor() as cursor:
        cursor.execute(
            "CALL l_catalogos_productos(%s, %s, %s)",
            [search, limit, offset]
        )

        total = utils.dictfetchall(cursor)[0]['total']
        cursor.nextset()
        productos = utils.dictfetchall(cursor)

    total_pages = (total + limit - 1) // limit

    return JsonResponse({
        "productos": productos,
        "page": page,
        "total_pages": total_pages
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

    search = request.GET.get('search', '').strip()
    page = int(request.GET.get('page', 1))

    limit = 20
    offset = (page - 1) * limit

    with connection.cursor() as cursor:
        cursor.execute(
            "CALL l_clientes(%s, %s, %s, %s, %s)",
            [is_staff, idvend, search, limit, offset]
        )

        total = utils.dictfetchall(cursor)[0]['total']
        cursor.nextset()
        clientes = utils.dictfetchall(cursor)

    total_pages = (total + limit - 1) // limit
    rango = range(max(1, page - 2), min(total_pages + 1, page + 3))

    return render(request, 'catalogo_clientes.html', {
        'clientes': clientes,
        'page': page,
        'total_pages': total_pages,
        'rango': rango,
        'search': search
    })

@login_required
def catalogo_clientes_ajax(request):

    is_staff = request.user.is_staff
    idvend = request.user.idvend

    search = request.GET.get('search', '').strip()
    page = int(request.GET.get('page', 1))

    limit = 20
    offset = (page - 1) * limit

    with connection.cursor() as cursor:
        cursor.execute(
            "CALL l_clientes(%s, %s, %s, %s, %s)",
            [is_staff, idvend, search, limit, offset]
        )

        total = utils.dictfetchall(cursor)[0]['total']
        cursor.nextset()
        clientes = utils.dictfetchall(cursor)

    total_pages = (total + limit - 1) // limit

    return JsonResponse({
        "clientes": clientes,
        "page": page,
        "total_pages": total_pages
    })


