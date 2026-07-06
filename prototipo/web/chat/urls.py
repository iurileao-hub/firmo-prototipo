from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("enviar/", views.enviar, name="enviar"),
    path("reiniciar/", views.reiniciar, name="reiniciar"),
]
