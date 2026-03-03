from django.urls import path
from . import views

urlpatterns = [
    path('productos/', views.catalogo_productos, name='productos'),
    path('productos/ajax/', views.catalogo_productos_ajax, name='catalogo_productos_ajax'),
    path('lineas/', views.catalogo_lineas, name='lineas'),
    path('sucursales/', views.catalogo_sucursales, name='sucursales'),
    path('grupos/', views.catalogo_grupos, name='grupos'),
    path('clientes/', views.catalogo_clientes, name='clientes'),
    path('clientes/ajax/', views.catalogo_clientes_ajax, name='catalogo_clientes_ajax')


]

