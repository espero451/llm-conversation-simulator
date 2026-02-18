import random
from django.core.management.base import BaseCommand
from django.db import transaction

from conversations.diet_rules import DIET_RULES_TEXT, classify_diet_rules
from conversations.llm import generate_text, generate_structured
from conversations.models import Conversation, Message

# ---------------- Prompt Instructions ----------------

WAITER_INSTRUCTIONS = (
    "You are a restaurant waiter. Be friendly and concise. "
    "Only write the waiter line, no role labels. "
    "Only greet once at the start, do not greet again."
)

CUSTOMER_INSTRUCTIONS = (
    "You are a restaurant customer. Be brief and natural. "
    "Follow the request and stay in character."
)


# ---------------- Schemas ----------------

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

DIET_CLASSIFY_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "diet": {"type": "string", "enum": ["omnivore", "vegetarian", "vegan"]},
        "reason": {"type": "string"},
    },
    "required": ["diet", "reason"],
}  # Diet classifier payload


# ---------------- Command ----------------

class Command(BaseCommand):
    help = "Simulate waiter/customer conversations"  # CLI description

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=100)  # Conversation count
        parser.add_argument(
            "--diet-mode",
            choices=["self", "rules", "llm"],
            default="self",
        )  # Diet source

    def handle(self, *args, **options):
        count = options["count"]
        diet_mode = options["diet_mode"]
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
                        "Ask the customer for their top 3 favorite foods. Do not greet or use salutations.",
                        WAITER_INSTRUCTIONS,
                    )
                    Message.objects.create(
                        conversation=conv,
                        role="waiter",
                        content=waiter_ask_fav,
                        turn_index=turn,
                    )
                    turn += 1

                    self_diet = random.choice(["omnivore", "vegetarian", "vegan"])  # Preselect diet
                    customer_fav = generate_structured(
                        (
                            f"Waiter asked: {waiter_ask_fav}\n"
                            f"Your diet is {self_diet}. "
                            "Set the JSON diet field to exactly this value.\n"
                            "Do not mention your diet or the words vegan/vegetarian/omnivore in the message.\n"
                            "Return 3 favorite foods that strictly match your diet.\n"
                            "Rules: vegan = no meat, fish, dairy, eggs, honey; "
                            "vegetarian = no meat or fish; omnivore = any foods.\n"
                            "Return JSON only."
                        ),
                        CUSTOMER_INSTRUCTIONS,
                        FAVORITES_SCHEMA,
                        "favorite_foods",
                    )
                    conv.favorite_foods = [food.strip().lower() for food in customer_fav["favorite_foods"]]  # Normalize
                    Message.objects.create(
                        conversation=conv,
                        role="customer",
                        content=customer_fav["message"],
                        turn_index=turn,
                    )
                    turn += 1

                    waiter_ask_order = generate_text(
                        "Ask what dishes the customer wants to order today. Do not greet or use salutations.",
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
                        (
                            f"Waiter asked: {waiter_ask_order}\n"
                            f"You previously said your diet is {self_diet}. "
                            f"{DIET_RULES_TEXT.get(self_diet, DIET_RULES_TEXT['omnivore'])}\n"
                            "Ordered dishes must strictly match your diet. Return JSON only."
                        ),
                        CUSTOMER_INSTRUCTIONS,
                        ORDER_SCHEMA,
                        "order",
                    )
                    conv.ordered_dishes = [dish.strip().lower() for dish in customer_order["ordered_dishes"]]  # Normalize
                    Message.objects.create(
                        conversation=conv,
                        role="customer",
                        content=customer_order["message"],
                        turn_index=turn,
                    )
                    final_diet = self_diet  # Default diet
                    if diet_mode == "rules":
                        final_diet = classify_diet_rules(
                            conv.favorite_foods,
                            conv.ordered_dishes,
                        ) or self_diet
                    elif diet_mode == "llm":
                        diet_check = generate_structured(
                            (
                                "You are the waiter. Classify the diet based on foods.\n"
                                f"Favorite foods: {conv.favorite_foods}\n"
                                f"Ordered dishes: {conv.ordered_dishes}\n"
                                "vegan = no meat, fish, dairy, eggs, honey; "
                                "vegetarian = no meat or fish; omnivore = any foods.\n"
                                "Return JSON only."
                            ),
                            WAITER_INSTRUCTIONS,
                            DIET_CLASSIFY_SCHEMA,
                            "diet_classification",
                        )
                        final_diet = diet_check["diet"]
                    conv.diet = final_diet  # Store final diet
                    conv.save()  # Persist extracted fields

                self.stdout.write(f"OK {i + 1}/{count}")  # Progress output
            except Exception as exc:
                self.stderr.write(f"FAIL {i + 1}/{count}: {exc}")  # Error report
