from django.urls import path

from .views import chatbot_ui, dashboard

# UI routes live outside the API namespace

urlpatterns = [
    path("chatbot/", chatbot_ui, name="chatbot_ui"),  # Chatbot UI page
    path("dashboard/", dashboard, name="dashboard"),  # Dashboard UI page
]
