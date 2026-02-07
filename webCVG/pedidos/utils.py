from django.db import connection

def dictfetchall(cursor):
    # Convierte fetchall() a una lista de dicts y puedes colocar los nombres completos del dato que necesitas.
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]

def get_catalogo_productos():
    with connection.cursor() as cursor:
        cursor.execute("CALL l_catalogos_productos()")
        return dictfetchall(cursor)

# MUESTRA LOS EVENTOS PARA PODER ASIGNARLOS DENTRO DEL PEDIDO
def get_eventos(): 
    with connection.cursor() as cursor:
        cursor.execute("CALL l_eventos()")
        return cursor.fetchall()
    
# MUESTRA LOS DATOS DEL CLIENTE PREVIAMENTE SELECCIONADO
def get_clientes(ide, idcliente):
    with connection.cursor() as cursor:
            cursor.execute("CALL c_cliente(%s, %s)", [ide, idcliente])
            row = cursor.fetchone()
                
            if not row:
                return None
                
            return {
                    'rfc': row[0],
                    'idcliente': row[1],
                    'razon_social': row[2],
                    'ruta': row[3]
                }
    
# MUESTRA LOS LISTADOS DE LOS CLIENTES ESTA PETICION GET SE ESTA UTILIZANDO TANTO PARA LA LISTA DE CLIENTES DE PEDIDO Y PARA LA LISTA DE CATALOGOS
def get_catalogo_clientes(is_staff, idvend):
     with connection.cursor() as cursor:
        cursor.execute("CALL l_clientes(%s, %s)", [is_staff, idvend])
        return dictfetchall(cursor)
     

# --- MUESTRA LOS PEDIDOS QUE ESTAN ACTIVOS SIN ENVIAR O EN ESTATUS PENDIENTE ---

def get_pedido_activo(idpedido, idvend, ide):
    with connection.cursor() as cursor:
        cursor.execute(
            "CALL c_pedido_activo(%s, %s, %s)",
            [idpedido, idvend, ide]
        )
        rows = dictfetchall(cursor)
        return rows[0] if rows else None

# --- MUESTRA LO PRODUCTOS DEL PEDIDO QUE ESTA ACTIVO SIN ENVIAR ---

def get_productos_pedido_activo(idpedido, ide):

    with connection.cursor() as cursor:
        cursor.execute(
            "CALL c_pedido_productos_activo(%s, %s)",
            [idpedido, ide]
        )
        return dictfetchall(cursor)


def get_pedido_activo_global(idvend, ide):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id
            FROM pedidos
            WHERE idvend = %s
              AND ide = %s
              AND status = 'PENDIENTE'
            ORDER BY id DESC
            LIMIT 1
        """, [idvend, ide])

        row = cursor.fetchone()
        return row[0] if row else None

# --- PARA ESTE PROCEDIMIENTO SE REALIZA UNA ACTUALIZACION DE STATUS PARA QUE CAMBIE DE PENDIENTE A CANCELADO
def cancelar_pedido(idpedido, idvend, ide):
    with connection.cursor() as cursor:
        cursor.execute(
            "CALL c_cancelar_pedido(%s, %s, %s)",
            [idpedido, idvend, ide]
        )

# ESTA TABLA ELIMINA LOS DATOS TEMPORALES
def limpiar_productos_seleccion(idpedido):
    with connection.cursor() as cursor:
        cursor.execute("""
            DELETE FROM pedido_productos_tmp
            WHERE id_pedido = %s
        """, [idpedido])


