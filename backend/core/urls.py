from django.urls import path

from . import views

urlpatterns = [
    path("dev/health", views.dev_health),
]
