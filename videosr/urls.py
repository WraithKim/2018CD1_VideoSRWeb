from django.urls import path
from . import views
app_name = 'test'

urlpatterns = [
    path('', views.index, name='index'),
    path('upload/', views.upload_test, name='upload_test'),
    path('upload/complete/', views.upload_complete, name='upload_complete'),
    path('download/', views.download_test, name='download_test'),
    path('download/<int:pk>/', views.download_file, name='download_file'),
    path('download/<int:pk>/delete/', views.delete_file, name='delete_file'),
    path('login/', views.login_test, name='login_test'),
    path('login/delete/', views.delete_account, name='delete_account'),
    path('payment/', views.payment_test, name='payment_test'),
    path('payment/<amount>/', views.payment_request, name='payment_request'),
    path('payment/<amount>/success/',views.payment_success, name='payment_success'),
    path('mq/', views.mq_test, name='mq_test'),
    path('mq/send/', views.mq_send, name='mq_send'),
    path('payment/fail/',views.payment_fail, name='payment_fail'),
]
