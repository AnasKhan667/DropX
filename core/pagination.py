"""
Custom DRF pagination.

StandardPagination is wired as the default in config/base.py.
Individual views can override page_size via the ?page_size= query param.
"""
from rest_framework.pagination import PageNumberPagination


class StandardPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
