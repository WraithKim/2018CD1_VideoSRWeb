from django.urls import path
from . import views
app_name = 'payment'

urlpatterns = [
    path('', views.index, name='index'),
    path('<amount>/', views.payment_request, name='payment_request'),
    path('<amount>/success/',views.payment_success, name='payment_success'),
    path('fail/',views.payment_fail, name='payment_fail'),
]