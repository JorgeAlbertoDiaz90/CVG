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
def lista_clientes_ajax(request):

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


# EN ESTE APARTADO SE CAPTURAN LOS DATOS PRINCIPALES DEL CLIENTE UNA VEZ SELECCIONADO EN EL PASO ANTERIOR Y SE REALIZA EL LLENADO AUTOMATICO


@login_required
def captura_propuesta(request, idcliente):
    ide = request.user.ide
    idvend = request.user.idvend

    # Fecha actual en UTC (correcto cuando USE_TZ = True)
    fecha_actual = timezone.localtime(timezone.now())

    with connection.cursor() as cursor:
        cursor.execute(
            "CALL a_pedido_inicial(%s, %s, %s, %s)",
            [idcliente, ide, idvend, fecha_actual]
        )
        result = utils.dictfetchall(cursor)

    idpedido = result[0]["id"]

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
    cliente = utils.get_clientes(pedido["idcliente"]) # FUNCIONANDO
    eventos = utils.get_eventos(pedido["idcliente"]) # FUNCIONANDO

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

    def to_decimal(valor, default="0"):
        try:
            return Decimal(str(valor))
        except:
            return Decimal(default)

    with transaction.atomic():
        with connection.cursor() as cursor:

            cursor.execute("""
                UPDATE pedidos
                SET n_evento = COALESCE(%s, n_evento),
                    observaciones = COALESCE(%s, observaciones),
                    total = %s
                WHERE id = %s
            """, [
                data.get("evento"),
                data.get("observaciones"),
                data.get("total", 0),
                data["id_pedido"]
            ])

            for p in data.get("productos", []):

                cantidad = Decimal(to_int(p.get("cantidad"), 1))

                cursor.execute("""
                    SELECT nombre, presentacion, publico
                    FROM productos
                    WHERE codigo = %s
                    LIMIT 1
                """, [p.get("codigo")])

                row = cursor.fetchone()
                if not row:
                    continue

                nombre, presentacion, precio = row
                precio = Decimal(precio)

                # Porcentajes
                d1_pct = to_decimal(p.get("d1"))
                d2_pct = to_decimal(p.get("d2"))
                bonificacion = to_decimal(p.get("bonificacion"))

                # ===== DESCUENTO 1 UNITARIO =====
                desc1_unit = precio * d1_pct / Decimal("100")
                base1 = precio - desc1_unit

                # ===== DESCUENTO 2 UNITARIO (factor) =====
                factor_d2 = Decimal("1") + (d2_pct / Decimal("100"))
                precio_neto = base1 / factor_d2 if factor_d2 > 0 else base1

                # Subtotal UNITARIO
                subtotal = precio_neto

                # Importe TOTAL
                importe = (subtotal * cantidad) - bonificacion

                # ===== DESCUENTOS TOTALES (por cantidad) =====
                desc2_unit = base1 - precio_neto

                desc1 = desc1_unit * cantidad
                desc2 = desc2_unit * cantidad

                # ===== Redondeo final =====
                subtotal = subtotal.quantize(Decimal("0.00"), rounding=ROUND_HALF_UP)
                desc1 = desc1.quantize(Decimal("0.00"), rounding=ROUND_HALF_UP)
                desc2 = desc2.quantize(Decimal("0.00"), rounding=ROUND_HALF_UP)
                importe = importe.quantize(Decimal("0.00"), rounding=ROUND_HALF_UP)

                observaciones = p.get("observaciones")
                observaciones = observaciones.strip() if observaciones else None

                cursor.execute(
                    "CALL a_pedido_producto(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    [
                        data["id_pedido"],
                        p.get("codigo"),
                        nombre,
                        presentacion,
                        precio,
                        cantidad,
                        bonificacion,
                        d1_pct,
                        desc1,
                        d2_pct,
                        desc2,
                        subtotal,
                        importe,
                        observaciones,
                        ide
                    ]
                )

    return JsonResponse({"ok": True})

@login_required
def limpiar_detalle_pedido(request):
        id_pedido = request.POST.get("id_pedido")

        with connection.cursor() as cursor:
            cursor.execute("CALL d_limpiar_productos_pedido(%s)", [id_pedido])

        return JsonResponse({"ok": True})


@login_required
def seleccion_multiple_productos(request, id_pedido):

    ide = request.user.ide
    idvend = request.user.idvend

    pedido = utils.get_pedido_activo(id_pedido, idvend, ide)

    if not pedido:
        messages.error(request, "Pedido inválido")
        return redirect("menu")

    if pedido["status"] != "PENDIENTE":
        messages.warning(request, "Este pedido ya no puede modificarse")
        return redirect("menu")

    # obtener evento desde querystring
    idev = int(request.GET.get("idev", 0))

    productos = utils.get_catalogo_productos(idev, ide)

    return render(request, "seleccion_multiple.html", {
        "id_pedido": id_pedido,
        "idcliente": pedido["idcliente"],
        "productos": productos,
        "idev": idev
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
@login_required
def buscar_productos(request):
    q = request.GET.get("q", "")
    idev = request.GET.get("idev")
    ide = request.user.ide

    with connection.cursor() as cursor:
        cursor.execute("CALL b_productos_evento(%s, %s, %s)", [q, ide, idev])
        rows = cursor.fetchall()

    resultado = [
        {
            "codigo": r[0],
            "nombre": r[1],
            "linea": r[2],
            "descripcion": r[3],
            "presentacion": r[4],
            "bon": r[5],
            "d1": r[6],
            "d2": r[7],
            "iva": r[8],
            "ieps": r[9],
            "publico": r[10],
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
            "cliente": r[1],
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

        # Si no viene evento o viene vacío -> 0

        evento = data.get("evento")
        if evento in (None, "", "null"):
            evento = 0

        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(
                    "CALL a_pedido_final(%s,%s,%s,%s,%s)",
                    [
                        data["id_pedido"],
                        data["ruta"],
                        int(evento),  # aseguramos entero
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
    is_staff = int(request.user.is_staff)

    search = request.GET.get('q', '').strip()
    page = int(request.GET.get('page', 1))

    limit = 20
    offset = (page - 1) * limit

    with connection.cursor() as cursor:
        cursor.execute(
            "CALL l_consultar_pedidos(%s, %s, %s, %s, %s)",
            [idvend, is_staff, search, limit, offset]
        )

        # Primer resultset: total
        total = utils.dictfetchall(cursor)[0]['total']

        # Segundo resultset: pedidos paginados
        cursor.nextset()
        pedidos = utils.dictfetchall(cursor)

    total_pages = (total + limit - 1) // limit

    rango = range(max(1, page - 2), min(total_pages + 1, page + 3))

    return render(request, 'consultar_pedidos.html', {
        'pedidos': pedidos,
        'page': page,
        'total_pages': total_pages,
        'rango': rango,
        'search': search,
        'es_staff': is_staff
    })

@login_required
def consultar_pedidos_ajax(request):
    idvend = request.user.idvend
    is_staff = int(request.user.is_staff)

    search = request.GET.get('q', '').strip()
    page = int(request.GET.get('page', 1))

    limit = 20
    offset = (page - 1) * limit

    with connection.cursor() as cursor:
        cursor.execute(
            "CALL l_consultar_pedidos(%s, %s, %s, %s, %s)",
            [idvend, is_staff, search, limit, offset]
        )

        total = utils.dictfetchall(cursor)[0]['total']
        cursor.nextset()
        pedidos = utils.dictfetchall(cursor)

    total_pages = (total + limit - 1) // limit

    return JsonResponse({
        "pedidos": pedidos,
        "page": page,
        "total_pages": total_pages
    })

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