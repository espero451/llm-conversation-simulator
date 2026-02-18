from django.urls import path

from .views import chatbot, simulations_latest, simulations_run, vegetarian_summary

# Routes live in the app for scalability

urlpatterns = [
    path("chatbot/", chatbot, name="chatbot"),  # Chatbot endpoint
    path("simulations/latest/", simulations_latest, name="simulations_latest"),  # Export
    path("simulations/run/", simulations_run, name="simulations_run"),  # Trigger sims
    path("vegetarians/", vegetarian_summary, name="vegetarians"),  # Vegetarian/vegan summary
]
