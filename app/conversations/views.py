import base64
import csv
import io
import json
import os
import secrets
from collections import Counter
from django.core.management import call_command
from django.db.models import Count
from django.http import JsonResponse, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from .llm import generate_text
from .models import Conversation


MAX_RUN_COUNT = 100  # Safety cap for sync runs
MAX_EXPORT_COUNT = 500  # Limit export payload
DASHBOARD_LATEST_COUNT = 100  # UI list size
TOP_FOODS_COUNT = 10  # Top foods per group
DIET_MODES = {"self", "rules", "llm"}  # Allowed diet modes


def _check_basic_auth(request):
    header = request.META.get("HTTP_AUTHORIZATION", "")
    if not header.startswith("Basic "):
        return False  # Missing auth header
    try:
        encoded = header.split(" ", 1)[1]
        decoded = base64.b64decode(encoded).decode("utf-8")
        user, _, password = decoded.partition(":")
    except (ValueError, UnicodeDecodeError):
        return False  # Bad auth header
    expected_user = os.environ.get("API_USER", "")
    expected_password = os.environ.get("API_PASSWORD", "")
    ok_user = secrets.compare_digest(user, expected_user)
    ok_pass = secrets.compare_digest(password, expected_password)
    return ok_user and ok_pass  # Verify credentials


def _require_basic_auth(request):
    if _check_basic_auth(request):
        return None  # Auth ok
    response = JsonResponse({"error": "Unauthorized"}, status=401)
    response["WWW-Authenticate"] = 'Basic realm="api"'
    return response  # Request auth


def _coerce_int(value, default, min_value, max_value):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default  # Fallback for bad input
    return max(min_value, min(parsed, max_value))  # Clamp to range


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
    return {diet: counter.most_common(top_n) for diet, counter in counters.items()}  # Top lists


def vegetarian_summary(request):
    auth_response = _require_basic_auth(request)
    if auth_response:
        return auth_response  # Enforce auth
    items = list(
        Conversation.objects.filter(diet__in=["vegetarian", "vegan"])
        .values("customer_label", "diet", "favorite_foods")
    )
    return JsonResponse({"count": len(items), "items": items})  # Return summary


def simulations_latest(request):
    auth_response = _require_basic_auth(request)
    if auth_response:
        return auth_response  # Enforce auth
    limit = _coerce_int(
        request.GET.get("limit"),
        DASHBOARD_LATEST_COUNT,
        1,
        MAX_EXPORT_COUNT,
    )
    export_format = request.GET.get("format", "json").lower()
    queryset = Conversation.objects.order_by("-created_at")[:limit]  # Latest sims
    if export_format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            ["id", "created_at", "customer_label", "diet", "favorite_foods", "ordered_dishes"]
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
        response["Content-Disposition"] = f'attachment; filename="simulations_latest_{limit}.csv"'
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


def simulations_run(request):
    auth_response = _require_basic_auth(request)
    if auth_response:
        return auth_response  # Enforce auth
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)  # Method guard
    count = _coerce_int(request.POST.get("count"), DASHBOARD_LATEST_COUNT, 1, MAX_RUN_COUNT)
    diet_mode = request.POST.get("diet-mode", "self")
    if diet_mode not in DIET_MODES:
        diet_mode = "self"  # Fallback for bad input
    call_command("simulate_conversations", count=count, diet_mode=diet_mode)  # Run sync command
    dashboard_url = reverse("dashboard")
    return redirect(f"{dashboard_url}?ran={count}")  # Return to dashboard


def dashboard(request):
    auth_response = _require_basic_auth(request)
    if auth_response:
        return auth_response  # Enforce auth
    latest_conversations = (
        Conversation.objects.order_by("-created_at")
        .prefetch_related("messages")[:DASHBOARD_LATEST_COUNT]
    )
    diet_counts = {diet: 0 for diet, _ in Conversation.DIET_CHOICES}  # Baseline
    for row in Conversation.objects.values("diet").annotate(count=Count("id")):
        diet_counts[row["diet"]] = row["count"]  # Fill counts
    top_foods = _top_foods_by_diet(
        Conversation.objects.values("diet", "favorite_foods"),
        TOP_FOODS_COUNT,
    )
    ran_count = _coerce_int(request.GET.get("ran"), 0, 0, MAX_RUN_COUNT)
    context = {
        "latest_conversations": latest_conversations,
        "diet_counts": diet_counts,
        "top_foods": top_foods,
        "ran_count": ran_count,
        "latest_limit": DASHBOARD_LATEST_COUNT,
    }
    return render(request, "conversations/dashboard.html", context)  # Render UI


def chatbot_ui(request):
    return render(request, "conversations/chatbot.html")  # Simple chat page


BOT_INSTRUCTIONS = (
    "You are a polite restaurant waiter. "
    "Ask the user what their top 3 favorite foods are. "
    "Keep it as an open question with an open answer."
)  # Bot behavior


@csrf_exempt
def chatbot(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)  # Method guard
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)  # Bad JSON
    user_input = payload.get("message", "")
    reply = generate_text(user_input, BOT_INSTRUCTIONS)  # LLM reply
    return JsonResponse({"reply": reply})  # API response
