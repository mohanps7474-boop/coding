from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('ai-assistant/', views.ai_assistant, name='ai_assistant'),
    path('chatbot/', views.chatbot_view, name='chatbot'),
    path('chatbot/bulk-email/', views.send_bulk_email, name='send_bulk_email'),
    path('chatbot/clear/', views.clear_chat_history, name='clear_chat_history'),
    path('analytics/', views.analytics_view, name='analytics'),
]
