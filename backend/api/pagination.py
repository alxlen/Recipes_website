from rest_framework.pagination import PageNumberPagination

from .constants import MAX_PAGE_SIZE, MAX_USERS_PAGE_SIZE, PAGE_SIZE


class CustomPagination(PageNumberPagination):
    page_size = PAGE_SIZE
    page_size_query_param = 'limit'
    max_page_size = MAX_PAGE_SIZE


class UserPagination(PageNumberPagination):
    page_size = MAX_USERS_PAGE_SIZE
    page_size_query_param = 'limit'
