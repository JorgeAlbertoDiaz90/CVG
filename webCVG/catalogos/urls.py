from django.urls import path
from . import views

urlpatterns = [
    path('productos/', views.catalogo_productos, name='productos'),
    path('lineas/', views.catalogo_lineas, name='lineas'),
    path('sucursales/', views.catalogo_sucursales, name='sucursales'),
    path('grupos/', views.catalogo_grupos, name='grupos'),
    path('clientes/', views.catalogo_clientes, name='clientes')


]

