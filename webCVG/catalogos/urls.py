from django.urls import path
from . import views

urlpatterns = [
    path('productos/', views.catalogo_productos, name='productos'),
    path('lineas/', views.catalogo_lineas, name='lineas'),
    path('sucursales/', views.catalogo_sucursales, name='sucursales'),
    path('proveedores/', views.catalogo_proveedores, name='proveedores'),
    path('clientes/', views.catalogo_clientes, name='clientes')


]

