from django.urls import path
from . import views

urlpatterns = [
    path('auth/', views.auth_view, name='auth'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('password-reset/', views.request_password_reset, name='password_reset'),
    path(
        'password-reset-confirm/<uidb64>/<token>/',
        views.password_reset_confirm,
        name='password_reset_confirm',
    ),
]
