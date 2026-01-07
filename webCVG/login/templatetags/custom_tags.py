from django import template
register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Accede a un valor dentro de un diccionario usando la clave"""
    if dictionary is None:
        return None
    return dictionary.get(key, None)
