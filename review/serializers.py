from rest_framework import serializers
from .models import Review

class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['review_id', 'delivery_id', 'reviewer_id', 'reviewed_id', 'rating', 'comment', 'review_type', 'created_at']
        read_only_fields = ['review_id', 'created_at']