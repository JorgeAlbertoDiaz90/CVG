from django.urls import path
from . import views

urlpatterns = [
    path('enchiladas/', views.signup, name='enchiladas'),
    path('logout/', views.signout, name='logout'),
    path('signin/', views.signin, name='signin'),
    path('menu/', views.menu, name='menu')
]