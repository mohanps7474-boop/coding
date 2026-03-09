from django.urls import path
from . import views

urlpatterns = [
    path('', views.campaign_list, name='campaign_list'),
    path('add/', views.campaign_create, name='campaign_create'),
]
