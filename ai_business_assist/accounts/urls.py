from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.handle_login, name='handle_login'),
    path('login_page/', views.handle_login, name='login_page'), # Added to support links in templates
    path('register/', views.register, name='register'),
    path('register_page/', views.register, name='register_page'), # Added to support links in templates
    path('logout/', views.handle_logout, name='handle_logout'),
    path('dashboard/', views.dashboard_view, name='dashboard_view'),
]
