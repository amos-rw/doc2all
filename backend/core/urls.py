from django.urls import path

from . import views

urlpatterns = [
    path("session", views.session),
    path("dev/health", views.dev_health),
]
