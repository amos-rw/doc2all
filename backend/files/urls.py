from django.urls import path

from . import views

urlpatterns = [
    path("files", views.upload),
    path("files/<str:file_id>", views.delete_file),
    path("files/<str:file_id>/download", views.download),
    path("jobs", views.start_job),
    path("jobs/<str:job_id>", views.job_state),
    path("jobs/<str:job_id>/report", views.report),
    path("history", views.history),
    path("history/<str:job_id>", views.remove_history),
]
