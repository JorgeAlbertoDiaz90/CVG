from django import template
register = template.Library()

@register.filter
def primeros_dos(value):
    if not value:
        return ""
    partes = value.split()
    return " ".join(partes[:2])

@register.filter
def money_es(value):
    """Formatea números como 25,910.80 (formato estándar) o 25.910,80 si deseas formato europeo."""
    try:
        # Asegurar que sea float
        number = float(value)
        # Formato con comas de miles y 2 decimales
        formatted = f"{number:,.2f}"
        # Si quieres formato latino (punto miles, coma decimal), descomenta la siguiente línea:
        # formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
        return formatted
    except (TypeError, ValueError):
        return value