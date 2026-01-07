from django.urls import path
from . import views

urlpatterns = [
    path('lista_cliente/', views.lista_cliente, name='lista_cliente'),
    path('captura_propuesta/<int:idcliente>/', views.captura_propuesta, name='captura_propuesta'),
    path("buscar_productos/", views.buscar_productos, name="buscar_productos"),
    path("guardar_pedido/", views.guardar_pedido, name='guardar_pedido'),
    path("historico_producto/", views.historico_producto, name='historico_producto'),
    path("consultar_pedidos/", views.consulta_pedidos, name='consultar_pedidos'),
    path("detalle_pedidos/<str:idpedido>/", views.pedidos_detalles, name="pedidos_detalles"),
    path("consultar_cliente/", views.consulta_cliente, name='consultar_cliente')

]