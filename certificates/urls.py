from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('profile/', views.profile, name='profile'),
    path('profile/delete/', views.delete_profile, name='delete_profile'),
    path('profile/photo/', views.view_profile_photo, name='view_profile_photo'),
    path('create-certificate/', views.create_certificate, name='create_certificate'),
    path('view-certificates/', views.view_certificates, name='view_certificates'),
    path('view-certificate/<str:certificate_id>/', views.view_certificate, name='view_certificate'),
    path('download-certificate/<str:certificate_id>/', views.download_certificate, name='download_certificate'),
    path('delete-certificate/<str:certificate_id>/', views.delete_certificate, name='delete_certificate'),
] 