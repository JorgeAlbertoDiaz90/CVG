from .utils import get_pedido_activo_global

def pedido_activo_global(request):
    if not request.user.is_authenticated:
        return {}

    ide = getattr(request.user, "ide", None)
    idvend = getattr(request.user, "idvend", None)

    if not ide or not idvend:
        return {}

    pedido_id = get_pedido_activo_global(idvend, ide)

    return {
        "pedido_activo": pedido_id
    }
