from rest_framework import serializers
from fdi.models import Investments


class InvestmentsSerializer(serializers.ModelSerializer):

    value = serializers.SerializerMethodField('get_investment_value')

    def get_investment_value(self, obj):
        val = getattr(obj, 'value')
        if val:
            return val

        if obj.approved_high_value:
            return 'high'
        elif obj.approved_good_value:
            return 'good'
        else:
            return 'standard'

    class Meta:
        model = Investments
        fields = '__all__'
        depth = 1
