from django.urls import path
from . import views

urlpatterns = [
    path('lista_cliente/', views.lista_cliente, name='lista_cliente'),
    path('captura_propuesta/<int:idcliente>/', views.captura_propuesta, name='captura_propuesta'),
    path('continuar_pedido/<int:idpedido>/', views.continuar_pedido, name='continuar_pedido'),
    path('guardar_borrador/', views.guardar_borrador_pedido, name='guardar_borrador_pedido'),
    path('buscar_productos/', views.buscar_productos, name='buscar_productos'),
    path('seleccion_multiple/<int:id_pedido>/', views.seleccion_multiple_productos, name='seleccion_multiple'),
    path("toggle_producto_seleccion/", views.toggle_producto_seleccion, name="toggle_producto_seleccion"),
    path("guardar_pedido/", views.guardar_pedido, name='guardar_pedido'),
    path("historico_producto/", views.historico_producto, name='historico_producto'),
    path("eliminar_producto_pedido/", views.eliminar_producto_pedido, name="eliminar_producto_pedido"),
    path("consultar_pedidos/", views.consulta_pedidos, name='consultar_pedidos'),
    path("detalle_pedidos/<str:idpedido>/", views.pedidos_detalles, name="pedidos_detalles"),
    path("consultar_cliente/", views.consulta_cliente, name='consultar_cliente'),
    path("cancelar_pedido/<int:idpedido>/", views.cancelar_pedido, name="cancelar_pedido")
]