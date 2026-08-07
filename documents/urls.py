from django.urls import path

from . import views

app_name = "documents"
urlpatterns = [
    path("", views.document_list, name="list"),
    path("upload/", views.manual_upload, name="upload"),
    path("<int:pk>/", views.viewer, name="viewer"),
    path("<int:pk>/preview/", views.preview, name="preview"),
    path("<int:pk>/download/", views.download, name="download"),
]
