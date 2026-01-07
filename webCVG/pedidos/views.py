from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db import connection, transaction
from . import utils
from django.utils import timezone
from django.contrib import messages
from django.http import JsonResponse
import json

# PARA ESTE APARTADO SE REALIZA UN LISTADO DE LOS CLIENTES DEPENDIENDO DEL VENDEDOR Y DE LA REGION DEL VENDEDOR

@login_required
def lista_cliente(request):
    is_staff = request.user.is_staff
    idvend = request.user.idvend

    try:
        clientes = utils.get_catalogo_clientes(is_staff, idvend)
    except Exception as e:
        messages.error(request, f"Error al cargar los clientes: {str(e)}")
    
    return render(request,'lista_cliente.html', {
        'clientes': clientes
    })


# --- COMIENZO DE INTERFAZ PARA CAPTURA DE PEDIDO ------

@login_required
def captura_propuesta(request, idcliente):
    ide = request.user.ide

    cliente = utils.get_clientes(ide, idcliente) # MUESTRA LOS DATOS DE CLIENTE SELECCIONADO
    evento = utils.get_eventos() # MUESTRA LOS EVENTOS PARA PODER ASIGNARLOS DENTRO DEL PEDIDO
    hoy = timezone.now() # AYUDA A MOSTRAR LA HORA Y ASIGNARLA DENTRO DEL PEDIDO

    return render(request, "captura_propuesta.html", {
        "clientes": cliente,
        "evento": evento,
        "fecha_hoy": hoy
    })

# PARA ESTE APARTADO SE REALIZARA LA BUSQUEDA DE PRODUCTOS POR MEDIO DE UN PROCEDIMIENTO ALMACENADO
def buscar_productos(request):
    q = request.GET.get("q", "")

    with connection.cursor() as cursor:
        cursor.execute("CALL b_productos(%s)", [q])
        rows = cursor.fetchall()

    resultado = [
        {
            "codigo": r[0],
            "nombre": r[1],
            "linea": r[2],
            "descripcion": r[3],
            "presentacion": r[4],
            "iva": r[5],
            "ieps": r[6],
            "publico": r[7],
        }
        for r in rows
    ]

    return JsonResponse(resultado, safe=False)

# PARA ESTE APARTADO SE MUESTRA UN HISTORICO DE LOS PRODUCTOS VENDIDOS PARA EL CLIENTE EN CUANTO SE ESTA REALIZANDO LA CAPTURA DEL PEDIDO

@login_required
def historico_producto(request):
    idvend = request.user.idvend
    idcliente = request.GET.get("idcliente")
    codigo = request.GET.get("codigo")

    with connection.cursor() as cursor:
        cursor.execute(
            "CALL l_pedidos_productos_historico(%s,%s,%s)",
            [idcliente, idvend, codigo]
        )
        rows = cursor.fetchall()

    data = [
        {
            "fecha": r[0],
            "pedido": r[1],
            "razon_social": r[2],
            "clave": r[3],
            "nombre": r[4],
            "precio": r[5],
            "cantidad": r[6],
            "bonificacion": r[7],
            "d1": r[8],
            "d2": r[9],
            "subtotal": r[10],
        }
        for r in rows
    ]

    return JsonResponse(data, safe=False)

# PARA ESTE APARTADO GUARDA EL PEDIDO COMPLETO TANTO EL PEDIDO EN GENERAL COMO LOS PRODUCTOS DEL PEDIDO Y ESTA CONECTADOS POR MEDIO DE id_pedido

def guardar_pedido(request):
    if request.method == "POST":
        data = json.loads(request.body)

        fecha = timezone.now()
        ide = request.user.ide
        idvend = request.user.idvend

        with transaction.atomic():
            with connection.cursor() as cursor:
                # =============================
                # 1. INSERTAR PEDIDO
                # =============================
                cursor.execute(
                    "CALL a_pedido(%s,%s,%s,%s,%s,%s,%s,%s)",
                    [
                        fecha,
                        data["idcliente"],
                        ide,
                        idvend,
                        data["ruta"],
                        data["evento"],
                        data["observaciones"],
                        data["total"]
                    ]
                )

                result = cursor.fetchone()
                id_pedido = result[0]

                # =============================
                # 2. INSERTAR PRODUCTOS
                # =============================
                for p in data["productos"]:
                    cursor.execute(
                        "CALL a_pedido_producto(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                        [
                            id_pedido,
                            p["codigo"],
                            p["nombre"],
                            p["precio"],
                            p["cantidad"],
                            p["d1"],
                            p["d2"],
                            p["subtotal"],
                            p["importe"],
                            p["comentario"],
                            ide
                        ]
                    )

        return JsonResponse({
            "ok": True,
            "id_pedido": id_pedido
        })
    

# ------ CIERRE DE CAPTURA DE PEDIDO -----

# ----- CONSULTAR PEDIDOS ------

@login_required
def consulta_pedidos(request):
    idvend = request.user.idvend
    is_staff = int(request.user.is_staff)  # Mejor como int para MySQL

    with connection.cursor() as cursor:
        cursor.execute(
            "CALL l_consultar_pedidos(%s, %s)",
            [idvend, is_staff]
        )
        pedidos = utils.dictfetchall(cursor)

    return render(
        request,
        'consultar_pedidos.html',
        {
            'pedidos': pedidos,
            'es_staff': is_staff 
        }
    )


@login_required
def pedidos_detalles(request, idpedido):

    with connection.cursor() as cursor:
        cursor.execute(
            "CALL l_consulta_pedidos_detalle(%s)",
            [idpedido]
        )
        detalle = utils.dictfetchall(cursor)

    return JsonResponse(detalle, safe=False)

# ---------- CONSULTAR CLIENTES -------------------

@login_required
def consulta_cliente(request):
    is_staff = request.user.is_staff
    idvend = request.user.idvend

    try:
        clientes = utils.get_catalogo_clientes(is_staff, idvend)

    except Exception as e:
        messages.error(request, f"Error: {str(e)}")
    
    return render(
        request,
        'consultar_cliente.html',
        {
            'clientes': clientes
        }
    )