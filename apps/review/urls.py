from django.urls import path
from .views import ReviewCreateView, ReviewDetailView, DriverReviewsListView

app_name = 'review'

urlpatterns = [
    path('', ReviewCreateView.as_view(), name='review-list-create'),
    path('driver/', DriverReviewsListView.as_view(), name='driver-reviews'),
    path('reviews/<uuid:review_id>/', ReviewDetailView.as_view(), name='review-detail'),
]

