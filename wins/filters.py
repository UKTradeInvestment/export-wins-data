from rest_framework import filters

from .models import CustomerResponse


class CustomerResponseFilterSet(filters.FilterSet):

    class Meta(object):
        model = CustomerResponse
        fields = ["win"]
