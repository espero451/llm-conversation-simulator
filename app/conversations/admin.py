from django.contrib import admin
from .models import Conversation, Message

# Register models for admin visibility
admin.site.register(Conversation)
admin.site.register(Message)
