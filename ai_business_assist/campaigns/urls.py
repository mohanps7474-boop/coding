from django.urls import path
from . import views

urlpatterns = [
    path('', views.campaign_list, name='campaign_list'),
    path('add/', views.campaign_create, name='campaign_create'),
    path('launch/<int:pk>/', views.campaign_launch, name='campaign_launch'),
    path('edit/<int:pk>/', views.campaign_edit, name='campaign_edit'),
    path('delete/<int:pk>/', views.campaign_delete, name='campaign_delete'),
    path('ai-suggest/', views.campaign_ai_suggest, name='campaign_ai_suggest'),
    path('check-scheduled/', views.check_scheduled_campaigns, name='check_scheduled_campaigns'),
]
