from rest_framework.pagination import CursorPagination


class DatasetViewCursorPagination(CursorPagination):
    """
    ID Cursor Pagination for generic Win relations
    """
    page_size = 100
    ordering = 'id'


class WinsDatasetViewCursorPagination(DatasetViewCursorPagination):
    """
    Cursor Pagination for WinsDatasetView
    """
    ordering = ('created', 'id')
