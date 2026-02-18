from django.urls import path

from .views import chatbot

# Routes live in the app for scalability
urlpatterns = [
    path("chatbot/", chatbot),  # Chatbot endpoint
]
