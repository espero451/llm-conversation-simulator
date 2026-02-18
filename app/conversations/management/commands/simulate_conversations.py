from django.core.management.base import BaseCommand
from django.db import transaction

from conversations.llm import generate_text, generate_structured
from conversations.models import Conversation, Message


WAITER_INSTRUCTIONS = (
    "You are a restaurant waiter. Be friendly and concise. "
    "Only write the waiter line, no role labels."
)  # Waiter role

CUSTOMER_INSTRUCTIONS = (
    "You are a restaurant customer. Be brief and natural. "
    "Follow the request and stay in character."
)  # Customer role

FAVORITES_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "message": {"type": "string"},
        "diet": {"type": "string", "enum": ["omnivore", "vegetarian", "vegan"]},
        "favorite_foods": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 3,
            "maxItems": 3,
        },
    },
    "required": ["message", "diet", "favorite_foods"],
}  # Favorites payload

ORDER_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "message": {"type": "string"},
        "ordered_dishes": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,
        },
    },
    "required": ["message", "ordered_dishes"],
}  # Order payload


class Command(BaseCommand):
    help = "Simulate waiter/customer conversations"  # CLI description

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=100)  # Conversation count

    def handle(self, *args, **options):
        count = options["count"]
        for i in range(count):
            try:
                with transaction.atomic():
                    conv = Conversation.objects.create(
                        customer_label=f"customer_{i + 1}",
                    )  # New conversation
                    turn = 1

                    waiter_greet = generate_text(
                        "Greet the customer and ask if they had a good day.",
                        WAITER_INSTRUCTIONS,
                    )
                    Message.objects.create(
                        conversation=conv,
                        role="waiter",
                        content=waiter_greet,
                        turn_index=turn,
                    )
                    turn += 1

                    customer_day = generate_text(
                        f"Waiter said: {waiter_greet}\nReply briefly about your day.",
                        CUSTOMER_INSTRUCTIONS,
                    )
                    Message.objects.create(
                        conversation=conv,
                        role="customer",
                        content=customer_day,
                        turn_index=turn,
                    )
                    turn += 1

                    waiter_ask_fav = generate_text(
                        "Ask the customer for their top 3 favorite foods.",
                        WAITER_INSTRUCTIONS,
                    )
                    Message.objects.create(
                        conversation=conv,
                        role="waiter",
                        content=waiter_ask_fav,
                        turn_index=turn,
                    )
                    turn += 1

                    customer_fav = generate_structured(
                        f"Waiter asked: {waiter_ask_fav}\nReturn JSON only.",
                        CUSTOMER_INSTRUCTIONS,
                        FAVORITES_SCHEMA,
                        "favorite_foods",
                    )
                    conv.diet = customer_fav["diet"]
                    conv.favorite_foods = customer_fav["favorite_foods"]
                    Message.objects.create(
                        conversation=conv,
                        role="customer",
                        content=customer_fav["message"],
                        turn_index=turn,
                    )
                    turn += 1

                    waiter_ask_order = generate_text(
                        "Ask what dishes the customer wants to order today.",
                        WAITER_INSTRUCTIONS,
                    )
                    Message.objects.create(
                        conversation=conv,
                        role="waiter",
                        content=waiter_ask_order,
                        turn_index=turn,
                    )
                    turn += 1

                    customer_order = generate_structured(
                        f"Waiter asked: {waiter_ask_order}\nReturn JSON only.",
                        CUSTOMER_INSTRUCTIONS,
                        ORDER_SCHEMA,
                        "order",
                    )
                    conv.ordered_dishes = customer_order["ordered_dishes"]
                    Message.objects.create(
                        conversation=conv,
                        role="customer",
                        content=customer_order["message"],
                        turn_index=turn,
                    )
                    conv.save()  # Persist extracted fields

                self.stdout.write(f"OK {i + 1}/{count}")  # Progress output
            except Exception as exc:
                self.stderr.write(f"FAIL {i + 1}/{count}: {exc}")  # Error report
