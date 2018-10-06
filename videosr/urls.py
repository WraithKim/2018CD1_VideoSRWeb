from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('upload/', views.upload_test, name='upload_test'),
    path('upload/complete/', views.upload_complete, name='upload_complete'),
    path('download/', views.download_test, name='download_test'),
    path('download/<int:pk>/', views.download_file, name='download_file'),
    path('download/<int:pk>/delete', views.delete_file, name='delete_file'),
]
