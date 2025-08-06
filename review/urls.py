from django.urls import path
from .views import ReviewCreateView, ReviewDetailView

app_name = 'review'

urlpatterns = [
    path('', ReviewCreateView.as_view(), name='review-list-create'),
    path('reviews/<uuid:review_id>/', ReviewDetailView.as_view(), name='review-detail'),
]

