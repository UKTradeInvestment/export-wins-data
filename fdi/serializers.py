from rest_framework import serializers
from fdi.models import Investments


class InvestmentsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Investments
        fields = '__all__'
        depth = 1
