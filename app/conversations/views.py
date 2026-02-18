import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .llm import generate_text


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
