from django.db import models


class Conversation(models.Model):
    DIET_CHOICES = [
        ("omnivore", "Omnivore"),
        ("vegetarian", "Vegetarian"),
        ("vegan", "Vegan"),
    ]  # Diet options for filtering

    created_at = models.DateTimeField(auto_now_add=True)  # Creation timestamp
    customer_label = models.CharField(max_length=64)  # Stable label per sim
    diet = models.CharField(
        max_length=16,
        choices=DIET_CHOICES,
        default="omnivore",
    )  # Diet tag for filters
    favorite_foods = models.JSONField(default=list)  # Top 3 foods
    ordered_dishes = models.JSONField(default=list)  # Orders in this convo

    def __str__(self):
        return f"Conversation {self.id} ({self.diet})"  # Admin label


class Message(models.Model):
    ROLE_CHOICES = [
        ("waiter", "Waiter"),
        ("customer", "Customer"),
    ]  # Speaker roles

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )  # Parent conversation
    role = models.CharField(max_length=16, choices=ROLE_CHOICES)  # Speaker role
    content = models.TextField()  # Raw message text
    turn_index = models.PositiveIntegerField()  # Order in conversation
    created_at = models.DateTimeField(auto_now_add=True)  # Creation timestamp

    class Meta:
        ordering = ["turn_index"]  # Stable transcript order
        unique_together = ("conversation", "turn_index")  # Prevent duplicates

    def __str__(self):
        return f"{self.conversation_id}:{self.turn_index} ({self.role})"  # Admin label
