from django_filters.rest_framework import FilterSet

from .models import CustomerResponse


class CustomerResponseFilterSet(FilterSet):

    class Meta(object):
        model = CustomerResponse
        fields = ["win"]
