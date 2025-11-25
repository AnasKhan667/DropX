from rest_framework import serializers
from .models import Review
from delivery.models import Delivery

class ReviewSerializer(serializers.ModelSerializer):

    class Meta:
        model = Review
        fields = [
            'review_id', 
            'delivery_id', 
            'reviewer_id', 
            'reviewed_id',
            'rating', 
            'comment', 
            'review_type', 
            'created_at'
        ]
        read_only_fields = ['review_id', 'created_at', 'reviewer_id', 'reviewed_id']

    def validate(self, data):
        request = self.context['request']
        delivery = data.get('delivery_id')

        # Delivery status check
        if delivery.status != "Delivered":
            raise serializers.ValidationError("You can only review completed deliveries.")

        # Auto-link reviewer/reviewed based on correct fields
        if request.user == delivery.sender_id:
            # Sender reviewing driver
            data['reviewer_id'] = request.user
            data['reviewed_id'] = delivery.driver_post_id.user
        elif request.user == delivery.driver_post_id.user:
            # Driver reviewing sender
            data['reviewer_id'] = request.user
            data['reviewed_id'] = delivery.sender_id
        else:
            raise serializers.ValidationError("You are not allowed to review this delivery.")

        # Rating validation
        rating = data.get('rating')
        if rating is None or not (1 <= rating <= 5):
            raise serializers.ValidationError("Rating must be between 1 and 5.")

        # Duplicate check
        if Review.objects.filter(delivery_id=delivery, reviewer_id=request.user).exists():
            raise serializers.ValidationError("You have already reviewed this delivery.")

        return data

