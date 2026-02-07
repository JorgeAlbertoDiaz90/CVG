from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db import connection, transaction
from . import utils
from django.utils import timezone
from datetime import datetime, timezone as dt_timezone
from django.contrib import messages
from django.http import JsonResponse
import json
from decimal import Decimal, ROUND_HALF_UP

# PARA ESTE APARTADO SE REALIZA UN LISTADO DE LOS CLIENTES DEPENDIENDO DEL VENDEDOR Y DE LA REGION DEL VENDEDOR
# *** Y ES EL PRIMER PASO PARA REALIZAR EL PEDIDO LA SELECCION DEL CLIENTE ***

@login_required
def lista_cliente(request):
    is_staff = request.user.is_staff
    idvend = request.user.idvend

    try:
        clientes = utils.get_catalogo_clientes(is_staff, idvend) # FUNCIONANDO
    except Exception as e:
        messages.error(request, f"Error al cargar los clientes: {str(e)}")
    
    return render(request,'lista_cliente.html', {
        'clientes': clientes
    })


# EN ESTE APARTADO SE CAPTURAN LOS DATOS PRINCIPALES DEL CLIENTE UNA VEZ SELECCIONADO EN EL PASO ANTERIOR Y SE REALIZA EL LLENADO AUTOMATICO

@login_required
def captura_propuesta(request, idcliente):
    ide = request.user.ide
    idvend = request.user.idvend

    with connection.cursor() as cursor:
        cursor.execute(
            "CALL a_pedido_inicial(%s, %s, %s)",
            [idcliente, ide, idvend]
        )
        result = utils.dictfetchall(cursor)

    # id del pedido creado o existente
    idpedido = result[0]["id"]

    # redirección correcta
    return redirect("continuar_pedido", idpedido=idpedido)

# PARA ESTE APARTADO ES LA CONTINUACION DE ALGUN PEDIDO QUE SE MANTENGA EN ESTATUS EN PENDIENTE

@login_required
def continuar_pedido(request, idpedido):
    ide = request.user.ide
    idvend = request.user.idvend

    pedido = utils.get_pedido_activo(idpedido, idvend, ide) # FUNCIONANDO

    if pedido["status"] != "PENDIENTE":
        messages.warning(request, "Este pedido ya no puede modificarse")
        return redirect("menu")
    
    # LIMPIAR TABLA TEMPORAL
    utils.limpiar_productos_seleccion(idpedido)

    productos = utils.get_productos_pedido_activo(idpedido, ide) # FUNCIONANDO
    cliente = utils.get_clientes(ide, pedido["idcliente"]) # FUNCIONANDO
    eventos = utils.get_eventos() # FUNCIONANDO

    fecha_raw = pedido.get("fecha")

    if fecha_raw:
        fecha_dt = datetime.strptime(fecha_raw, "%Y-%m-%d %H:%M:%S")

        # ASUMES QUE ES UTC
        fecha_dt = timezone.make_aware(fecha_dt, dt_timezone.utc)

        # Se convierte a hora local (America/Mexico_City)
        fecha_pedido = timezone.localtime(fecha_dt)
    else:
        fecha_pedido = timezone.localtime(timezone.now())

    return render(request, "captura_propuesta.html", {
        "pedido": pedido,
        "productos": productos,
        "clientes": cliente,
        "evento": eventos,
        "fecha_pedido": fecha_pedido,
        #"productos_seleccion": productos_seleccion
    })

def to_decimal(valor, default="0.00"):
    try:
        return Decimal(str(valor))
    except:
        return Decimal(default)


@login_required
def guardar_borrador_pedido(request):
    if request.method != "POST":
        return JsonResponse({"ok": False}, status=405)

    data = json.loads(request.body)
    ide = request.user.ide

    def to_int(valor, default=1):
        try:
            return int(valor)
        except:
            return default

    with transaction.atomic():
        with connection.cursor() as cursor:

            for p in data.get("productos", []):

                cantidad = Decimal(to_int(p.get("cantidad"), 1))

                # DATOS REALES DEL PRODUCTO
                cursor.execute("""
                    SELECT nombre, presentacion, publico
                    FROM productos
                    WHERE codigo = %s
                    LIMIT 1
                """, [p.get("codigo")])

                row = cursor.fetchone()
                if not row:
                    continue

                nombre = row[0]
                presentacion = row[1]
                precio = Decimal(row[2])

                # PORCENTAJES (SE GUARDAN ASÍ)
                d1_pct = to_decimal(p.get("d1"))   # ej. 5
                d2_pct = to_decimal(p.get("d2"))   # ej. 10
                bonificacion = to_decimal(p.get("bonificacion"))

                # SUBTOTAL
                subtotal = (precio * cantidad).quantize(
                    Decimal("0.00"),
                    rounding=ROUND_HALF_UP
                )

                # CÁLCULO INTERNO (NO SE GUARDA)
                desc1 = (subtotal * d1_pct / Decimal("100")).quantize(
                    Decimal("0.00"),
                    rounding=ROUND_HALF_UP
                )

                desc2 = (subtotal * d2_pct / Decimal("100")).quantize(
                    Decimal("0.00"),
                    rounding=ROUND_HALF_UP
                )

                # IMPORTE FINAL
                importe = (subtotal - desc1 - desc2 - bonificacion).quantize(
                    Decimal("0.00"),
                    rounding=ROUND_HALF_UP
                )

                observaciones = p.get("observaciones")
                observaciones = observaciones.strip() if observaciones else None

                cursor.execute(
                    "CALL a_pedido_producto(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    [
                        data["id_pedido"],
                        p.get("codigo"),
                        nombre,
                        presentacion,
                        precio,
                        cantidad,
                        bonificacion,
                        d1_pct,      # SE GUARDA EL %
                        d2_pct,      # SE GUARDA EL %
                        subtotal,
                        importe,
                        observaciones,
                        ide
                    ]
                )

    return JsonResponse({"ok": True})



@login_required
def seleccion_multiple_productos(request, id_pedido):

    ide = request.user.ide
    idvend = request.user.idvend

    # Reutilizamos la misma lógica que continuar_pedido
    pedido = utils.get_pedido_activo(id_pedido, idvend, ide)

    if not pedido:
        messages.error(request, "Pedido inválido")
        return redirect("menu")

    if pedido["status"] != "PENDIENTE":
        messages.warning(request, "Este pedido ya no puede modificarse")
        return redirect("menu")

    productos = utils.get_catalogo_productos()

    return render(request, "seleccion_multiple.html", {
        "id_pedido": id_pedido,
        "idcliente": pedido["idcliente"], 
        "productos": productos
    })

@login_required
def toggle_producto_seleccion(request):
    if request.method != "POST":
        return JsonResponse({"ok": False}, status=405)

    data = json.loads(request.body)

    with connection.cursor() as cursor:
        if data["activo"]:
            cursor.execute("""
                INSERT IGNORE INTO pedido_productos_tmp (id_pedido, codigo_producto)
                VALUES (%s, %s)
            """, [data["id_pedido"], data["codigo"]])
        else:
            cursor.execute("""
                DELETE FROM pedido_productos_tmp
                WHERE id_pedido = %s AND codigo_producto = %s
            """, [data["id_pedido"], data["codigo"]])

    return JsonResponse({"ok": True})


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
    ide = request.user.ide
    idcliente = request.GET.get("idcliente")
    codigo = request.GET.get("codigo")

    with connection.cursor() as cursor:
        cursor.execute(
            "CALL l_pedidos_productos_historico(%s,%s,%s)",
            [idcliente, ide, codigo]
        )
        rows = cursor.fetchall()
        cursor.nextset()
        
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

@login_required
def eliminar_producto_pedido(request):
    if request.method == "POST":
        data = json.loads(request.body)

        with connection.cursor() as cursor:
            cursor.execute("""
                DELETE FROM pedidos_productos
                WHERE id_pedido = %s
                  AND clave_producto = %s
            """, [data["id_pedido"], data["codigo"]])

        return JsonResponse({"ok": True})


# PARA ESTE APARTADO GUARDA EL PEDIDO COMPLETO TANTO EL PEDIDO EN GENERAL COMO LOS PRODUCTOS DEL PEDIDO Y ESTA CONECTADOS POR MEDIO DE id_pedido

@login_required
def guardar_pedido(request):
    if request.method == "POST":
        data = json.loads(request.body)
        ide = request.user.ide

        with transaction.atomic():
            with connection.cursor() as cursor:
                
                # FINALIZAR PEDIDO
                cursor.execute(
                    "CALL a_pedido_final(%s,%s,%s,%s,%s)",
                    [
                        data["id_pedido"],
                        data["ruta"],
                        data["evento"],
                        data["observaciones"],
                        data["total"]
                    ]
                )

        return JsonResponse({
            "ok": True,
            "id_pedido": data["id_pedido"]
        })


@login_required
def cancelar_pedido(request, idpedido):
    ide = request.user.ide
    idvend = request.user.idvend

    pedido = utils.get_pedido_activo(idpedido, idvend, ide)

    if not pedido:
        messages.error(request, "El pedido no puede cancelarse")
        return redirect("menu")

    utils.cancelar_pedido(idpedido, idvend, ide)

    messages.success(
        request,
        f"Pedido {idpedido} cancelado correctamente"
    )

    return redirect("menu")

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