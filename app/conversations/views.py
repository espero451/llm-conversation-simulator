import csv
import io
import os
from collections import Counter
from django.contrib.auth.decorators import login_required, permission_required
from django.core.management import call_command
from django.db.models import Count
from django.http import JsonResponse, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .constants import (
    DASHBOARD_LATEST_COUNT,
    TOP_FOODS_COUNT,
)
from .llm import generate_text
from .models import Conversation
from .serializers import (
    ChatbotPayloadSerializer,
    DashboardQuerySerializer,
    SimulationsLatestQuerySerializer,
    SimulationsRunSerializer,
)


# Aggregate top foods per diet from conversation rows.
def _top_foods_by_diet(rows, top_n):
    counters = {diet: Counter() for diet, _ in Conversation.DIET_CHOICES}  # Buckets
    for row in rows:
        diet = row.get("diet")
        foods = row.get("favorite_foods") or []
        if diet not in counters:
            continue  # Skip unknown diet
        for food in foods:
            if not food:
                continue  # Skip blanks
            normalized = str(food).strip().lower()
            if not normalized:
                continue  # Skip empty
            counters[diet][normalized] += 1  # Count foods
    return {
        diet: counter.most_common(top_n) for diet, counter in counters.items()
    }  # Top lists


# Serve vegetarian/vegan summaries with favorite foods.
@login_required
@permission_required("conversations.view_conversation", raise_exception=True)
def vegetarian_summary(request):
    items = list(
        Conversation.objects.filter(diet__in=["vegetarian", "vegan"]).values(
            "customer_label", "diet", "favorite_foods"
        )
    )
    return JsonResponse({"count": len(items), "items": items})  # Return summary


# Export latest simulations in JSON or CSV.
@login_required
@permission_required("conversations.view_conversation", raise_exception=True)
def simulations_latest(request):
    serializer = SimulationsLatestQuerySerializer(data=request.GET)
    if not serializer.is_valid():
        return JsonResponse(serializer.errors, status=400)  # Invalid query
    limit = serializer.validated_data["limit"]
    export_format = serializer.validated_data["format"]
    queryset = Conversation.objects.order_by("-created_at")[:limit]  # Latest sims
    if export_format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "id",
                "created_at",
                "customer_label",
                "diet",
                "favorite_foods",
                "ordered_dishes",
            ]
        )
        for convo in queryset:
            writer.writerow(
                [
                    convo.id,
                    convo.created_at.isoformat(),
                    convo.customer_label,
                    convo.diet,
                    "|".join(str(food) for food in (convo.favorite_foods or [])),
                    "|".join(str(dish) for dish in (convo.ordered_dishes or [])),
                ]
            )
        response = HttpResponse(output.getvalue(), content_type="text/csv")
        response["Content-Disposition"] = (
            f'attachment; filename="simulations_latest_{limit}.csv"'
        )
        return response  # Send CSV download
    items = list(
        queryset.values(
            "id",
            "created_at",
            "customer_label",
            "diet",
            "favorite_foods",
            "ordered_dishes",
        )
    )
    return JsonResponse({"count": len(items), "items": items})  # Send JSON payload


# Trigger a sync simulation run from a POST request.
@login_required
@permission_required("conversations.add_conversation", raise_exception=True)
def simulations_run(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)  # Method guard
    payload = request.POST.copy()
    if "diet-mode" in payload and "diet_mode" not in payload:
        payload["diet_mode"] = payload["diet-mode"]  # Map form field name
    serializer = SimulationsRunSerializer(data=payload)
    if not serializer.is_valid():
        return JsonResponse(serializer.errors, status=400)  # Invalid payload
    count = serializer.validated_data["count"]
    diet_mode = serializer.validated_data["diet_mode"]
    call_command(
        "simulate_conversations", count=count, diet_mode=diet_mode
    )  # Run sync command
    dashboard_url = reverse("dashboard")
    return redirect(f"{dashboard_url}?ran={count}")  # Return to dashboard


# Render the dashboard with metrics and recent conversations.
@login_required
@permission_required("conversations.view_conversation", raise_exception=True)
def dashboard(request):
    latest_conversations = Conversation.objects.order_by(
        "-created_at"
    ).prefetch_related("messages")[:DASHBOARD_LATEST_COUNT]
    diet_counts = {diet: 0 for diet, _ in Conversation.DIET_CHOICES}  # Baseline
    for row in Conversation.objects.values("diet").annotate(count=Count("id")):
        diet_counts[row["diet"]] = row["count"]  # Fill counts
    top_foods = _top_foods_by_diet(
        Conversation.objects.values("diet", "favorite_foods"),
        TOP_FOODS_COUNT,
    )
    serializer = DashboardQuerySerializer(data=request.GET)
    serializer.is_valid()  # Keep dashboard usable with invalid query params
    ran_count = serializer.validated_data.get("ran", 0)
    context = {
        "latest_conversations": latest_conversations,
        "diet_counts": diet_counts,
        "top_foods": top_foods,
        "ran_count": ran_count,
        "latest_limit": DASHBOARD_LATEST_COUNT,
    }
    return render(request, "conversations/dashboard.html", context)  # Render UI


# Render the chatbot UI page.
@login_required
@permission_required("conversations.view_conversation", raise_exception=True)
def chatbot_ui(request):
    return render(request, "conversations/chatbot.html")  # Simple chat page


BOT_INSTRUCTIONS = (
    "You are a polite restaurant waiter. "
    "Ask the user what their top 3 favorite foods are. "
    "Keep it as an open question with an open answer."
)

class ChatbotAPIView(APIView):
    authentication_classes = [SessionAuthentication]  # Enforce CSRF for sessions
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs) -> Response:
        serializer = ChatbotPayloadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_input = serializer.validated_data["message"]
        reply = generate_text(user_input, BOT_INSTRUCTIONS)

        return Response({"reply": reply}, status=status.HTTP_200_OK)


chatbot = ChatbotAPIView.as_view()
