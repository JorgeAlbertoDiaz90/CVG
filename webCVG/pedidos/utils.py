from django.db import connection

def dictfetchall(cursor):
    # Convierte fetchall() a una lista de dicts y puedes colocar los nombres completos del dato que necesitas.
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]

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
     

