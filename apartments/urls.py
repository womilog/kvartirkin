from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('apartments/', views.apartment_list, name='apartment_list'),
    path('apartment/<slug:slug>/', views.apartment_detail, name='apartment_detail'),
    path('apartment/<slug:slug>/booking/', views.booking, name='booking'),
    path('booking/success/', views.booking_success, name='booking_success'),
    path('apartment/<slug:slug>/check-availability/', views.check_availability, name='check_availability'),
]
