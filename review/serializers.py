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

        # Must be delivery completed
        if delivery.status != "Delivered":
            raise serializers.ValidationError("You can only review completed deliveries.")

        # Reviewer MUST be the sender for this delivery
        if delivery.user != request.user:
            raise serializers.ValidationError("You can only review deliveries you created.")

        # Reviewed user MUST be the driver
        data['reviewer_id'] = request.user
        data['reviewed_id'] = delivery.driver_post_id.user

        # Rating must be 1-5
        rating = data.get('rating')
        if rating < 1 or rating > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")

        # Prevent duplicate review
        if Review.objects.filter(delivery_id=delivery, reviewer_id=request.user).exists():
            raise serializers.ValidationError("You have already reviewed this delivery.")

        return data
