import json
import base64
import os
import secrets
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .llm import generate_text
from .models import Conversation


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


def vegetarian_summary(request):
    if not _check_basic_auth(request):
        response = JsonResponse({"error": "Unauthorized"}, status=401)
        response["WWW-Authenticate"] = 'Basic realm="api"'
        return response  # Request auth
    items = list(
        Conversation.objects.filter(diet__in=["vegetarian", "vegan"])
        .values("customer_label", "diet", "favorite_foods")
    )
    return JsonResponse({"count": len(items), "items": items})  # Return summary


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
