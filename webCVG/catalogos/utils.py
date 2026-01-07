from django.db import connection

def dictfetchall(cursor):
    # Convierte fetchall() a una lista de dicts
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]