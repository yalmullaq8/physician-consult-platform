from rest_framework import serializers

from .models import Booking


class BookingCreateSerializer(serializers.Serializer):
    consulting_physician_id = serializers.IntegerField()
    scheduled_start = serializers.DateTimeField()
    case_summary = serializers.CharField()
    requester_name = serializers.CharField(max_length=255)
    requester_specialization = serializers.CharField(max_length=255)
    requester_country_of_practice = serializers.CharField(max_length=100)
    requester_email = serializers.EmailField()
    requester_whatsapp_number = serializers.CharField(max_length=30, required=False, allow_blank=True)
    payment_method_id = serializers.IntegerField(required=False, allow_null=True)


class BookingSerializer(serializers.ModelSerializer):
    requesting_physician_name = serializers.CharField(source="requesting_physician.full_name", read_only=True)
    consulting_physician_name = serializers.CharField(source="consulting_physician.full_name", read_only=True)

    class Meta:
        model = Booking
        fields = [
            "booking_reference",
            "requesting_physician",
            "requesting_physician_name",
            "consulting_physician",
            "consulting_physician_name",
            "scheduled_start",
            "scheduled_end",
            "status",
            "case_summary",
            "requester_name",
            "requester_specialization",
            "requester_country_of_practice",
            "requester_email",
            "requester_whatsapp_number",
            "meeting_url",
            "cancellation_reason",
            "cancelled_at",
            "created_at",
            "updated_at",
        ]
