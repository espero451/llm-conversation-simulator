from rest_framework import serializers

from .constants import (
    DASHBOARD_LATEST_COUNT,
    DIET_MODES,
    MAX_EXPORT_COUNT,
    MAX_RUN_COUNT,
)

# --- Query Serializers ------------------------------------------------

# Validate query params for latest simulations exports.
class SimulationsLatestQuerySerializer(serializers.Serializer):
    limit = serializers.IntegerField(
        required=False,
        default=DASHBOARD_LATEST_COUNT,
        min_value=1,
        max_value=MAX_EXPORT_COUNT,
    )
    format = serializers.CharField(required=False, default="json")

    def validate_format(self, value: str) -> str:
        normalized = value.lower()  # Normalize export format to lowercase
        if normalized not in {"json", "csv"}:
            raise serializers.ValidationError("Format must be json or csv.")
        return normalized


# Validate query params for dashboard counters.
class DashboardQuerySerializer(serializers.Serializer):
    ran = serializers.IntegerField(
        required=False,
        default=0,
        min_value=0,
        max_value=MAX_RUN_COUNT,
    )


# --- Payload Serializers ----------------------------------------------

# Validate POST form payload for simulation runs.
class SimulationsRunSerializer(serializers.Serializer):
    count = serializers.IntegerField(
        required=False,
        default=DASHBOARD_LATEST_COUNT,
        min_value=1,
        max_value=MAX_RUN_COUNT,
    )
    diet_mode = serializers.ChoiceField(
        required=False,
        choices=sorted(DIET_MODES),
        default="self",
    )


# Validate JSON payload for chatbot messages.
class ChatbotPayloadSerializer(serializers.Serializer):
    message = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
    )
