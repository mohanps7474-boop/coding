from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.handle_login, name='handle_login'),
    path('login_page/', views.handle_login, name='login_page'), # Added to support links in templates
    path('register/', views.register, name='register'),
    path('register_page/', views.register, name='register_page'), # Added to support links in templates
    path('logout/', views.handle_logout, name='handle_logout'),
    path('dashboard/', views.dashboard_view, name='dashboard_view'),
    path('front/', views.front_page, name='front_page'),
    path('setup_form/', views.form_page, name='form_page'),
    path('portfolio/', views.landing_view, name='portfolio'),
    path('test-email/', views.test_email_view, name='test_email'),
    path('gmail/', views.gmail_view, name='gmail_view'),
    path('settings/', views.settings_view, name='settings'),
    path('about/', views.about_view, name='about'),
]
