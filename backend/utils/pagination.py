from rest_framework.pagination import PageNumberPagination

class CustomPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 1000

    def paginate_queryset(self, queryset, request, view=None):
        if request.query_params.get('nopage') == 'true':
            return None
        return super().paginate_queryset(queryset, request, view)
