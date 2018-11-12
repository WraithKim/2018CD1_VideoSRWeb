from django.urls import path
from . import views
app_name = 'dashboard'

urlpatterns = [
    path('', views.index, name='index'),
    path('upload/complete/', views.upload_complete, name='upload_complete'),
    path('download/<int:pk>/', views.download_file, name='download_file'),
    path('download/<int:pk>/delete/', views.delete_file, name='delete_file'),
    path('settings/delete_account/', views.delete_account, name='delete_account'),
    path('settings/', views.user_settings, name='user_settings'),
]
