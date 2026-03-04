from django.urls import path

from .views import (
    ChatbotAPIView,
    simulations_latest,
    simulations_run,
    vegetarian_summary,
)

# Routes live in the app for scalability

urlpatterns = [
    path("chatbot/", ChatbotAPIView.as_view(), name="chatbot"),  # Chatbot endpoint
    path("simulations/latest/", simulations_latest, name="simulations_latest"),  # Export
    path("simulations/run/", simulations_run, name="simulations_run"),  # Trigger sims
    path("vegetarians/", vegetarian_summary, name="vegetarians"),  # Vegetarian/vegan summary
]
