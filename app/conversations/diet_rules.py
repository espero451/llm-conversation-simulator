import re

MEAT_KEYWORDS = {
    "beef",
    "pork",
    "lamb",
    "veal",
    "ham",
    "bacon",
    "sausage",
    "steak",
    "turkey",
    "chicken",
    "duck",
    "fish",
    "salmon",
    "tuna",
    "cod",
    "trout",
    "shrimp",
    "prawn",
    "crab",
    "lobster",
    "anchovy",
}  # Detect meat or fish signals

ANIMAL_PRODUCT_KEYWORDS = {
    "cheese",
    "milk",
    "butter",
    "cream",
    "yogurt",
    "egg",
    "eggs",
    "honey",
}  # Detect dairy or eggs

DIET_RULES_TEXT = {
    "vegan": "Vegan: no meat, fish, dairy, eggs, or honey.",
    "vegetarian": "Vegetarian: no meat or fish; dairy and eggs allowed.",
    "omnivore": "Omnivore: any foods allowed.",
}  # Prompt rules for diet

TOKEN_RE = re.compile(r"\b[\w']+\b", re.UNICODE)  # Extract word tokens


def _tokenize(text):
    cleaned = text.replace("-", " ")  # Split hyphenated words
    return set(TOKEN_RE.findall(cleaned.lower()))  # Normalize tokens


def _collect_tokens(items):
    tokens = set()
    for item in items or []:
        if not item:
            continue  # Skip blanks
        tokens |= _tokenize(str(item))
    return tokens  # Combined tokens


def classify_diet_rules(favorite_foods, ordered_dishes):
    tokens = _collect_tokens(favorite_foods) | _collect_tokens(ordered_dishes)
    if not tokens:
        return None  # No evidence
    if tokens & MEAT_KEYWORDS:
        return "omnivore"  # Meat or fish found
    if tokens & ANIMAL_PRODUCT_KEYWORDS:
        return "vegetarian"  # Animal product found
    return "vegan"  # Plant-only default
