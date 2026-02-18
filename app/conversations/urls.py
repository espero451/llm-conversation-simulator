from django.urls import path

from .views import chatbot, vegetarian_summary

# Routes live in the app for scalability

urlpatterns = [
    path("chatbot/", chatbot),  # Chatbot endpoint
    path("vegetarians/", vegetarian_summary),  # Vegetarian/vegan summary
]
