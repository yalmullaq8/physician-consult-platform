from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import AvailabilityException, PhysicianAvailability, PhysicianProfile, Specialty


class SpecialtySerializer(serializers.ModelSerializer):
    class Meta:
        model = Specialty
        fields = ["id", "name", "slug", "description", "display_order"]


class PhysicianListSerializer(serializers.ModelSerializer):
    specialties = SpecialtySerializer(many=True, read_only=True)

    class Meta:
        model = PhysicianProfile
        fields = [
            "id",
            "full_name",
            "slug",
            "specialties",
            "professional_title",
            "consultation_price",
            "consultation_duration_minutes",
            "bio",
            "profile_photo",
            "is_featured",
        ]


class PhysicianDetailSerializer(serializers.ModelSerializer):
    specialties = SpecialtySerializer(many=True, read_only=True)

    class Meta:
        model = PhysicianProfile
        fields = [
            "id",
            "full_name",
            "slug",
            "specialties",
            "subspecialty",
            "professional_title",
            "hospital_or_clinic",
            "years_of_experience",
            "consultation_price",
            "consultation_duration_minutes",
            "bio",
            "profile_photo",
            "is_featured",
        ]


class PhysicianAvailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = PhysicianAvailability
        fields = ["id", "weekday", "start_time", "end_time", "is_active"]

    def create(self, validated_data):
        try:
            return super().create(validated_data)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict if hasattr(exc, "message_dict") else exc.messages)


class AvailabilityExceptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AvailabilityException
        fields = ["id", "date", "start_time", "end_time", "exception_type", "reason"]

    def create(self, validated_data):
        try:
            return super().create(validated_data)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict if hasattr(exc, "message_dict") else exc.messages)