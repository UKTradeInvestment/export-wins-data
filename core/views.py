from datetime import datetime

from django.core.exceptions import ObjectDoesNotExist

from django.utils.timezone import now
from pytz import UTC
from rest_framework import status
from rest_framework.exceptions import ParseError, NotFound
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from mi.models import FinancialYear
from mi.serializers import DateRangeSerializer

from alice.authenticators import IsMIServer, IsMIUser

MI_PERMISSION_CLASSES = (IsMIServer, IsMIUser)


class BaseMIView(GenericAPIView):
    """ Base view for other MI endpoints to inherit from """

    permission_classes = MI_PERMISSION_CLASSES
    fin_year = None
    date_range = None

    date_start = None
    date_end = None

    def _handle_fin_year(self, request):
        """
        Checks and makes sure if year query param is supplied within request object
        Obtains FinancialYear model out of it and stores it for subclasses to use
        Returns 404 if FinancialYear is not found
        """
        year = request.GET.get("year", None)
        if not year:
            self._invalid("missing argument: year")
        try:
            year = int(year)
            self.fin_year = FinancialYear.objects.get(id=year)
        except (ObjectDoesNotExist, ValueError):
            self._not_found()

    def _date_range_start(self):
        """
        Financial year start date, as datetime, is returned
        """
        if self.date_start:
            return self.date_start

        return datetime.combine(self.fin_year.start, datetime.min.time()).replace(tzinfo=UTC)

    def _date_range_end(self):
        """
        If fin_year is not current one, current datetime is returned
        Else financial year end date, as datetime, is returned
        """
        if self.date_end:
            return self.date_end

        if datetime.today().replace(tzinfo=UTC) < self.fin_year.end:
            return now()
        else:
            return datetime.combine(self.fin_year.end, datetime.max.time()).replace(tzinfo=UTC)

    def _fill_date_ranges(self):
        """
        This sets up date_range for response using _date_range_start
        and _date_range_end functions, as epoch
        """
        self.date_range = {
            "start": self._date_range_start(),
            "end": self._date_range_end(),
        }

    def _invalid(self, msg):
        raise ParseError({'error': msg})

    def _success(self, results, **extra):
        if self.fin_year is not None:
            response = {
                "timestamp": now(),
                "financial_year": {
                    "id": self.fin_year.id,
                    "description": self.fin_year.description,
                },
                "results": results,
                **extra
            }

            if self.date_range is not None:
                response["date_range"] = self.date_range

        else:
            response = results

        return Response(response, status=status.HTTP_200_OK)

    def _not_found(self, detail=None):
        raise NotFound(detail=detail)

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        self._handle_fin_year(request)
        self._handle_query_param_dates(request)
        self._fill_date_ranges()

    def _handle_query_param_dates(self, request):
        serializer = DateRangeSerializer(
            financial_year=self.fin_year, data=request.GET)
        if serializer.is_valid():
            for param, value in serializer.validated_data.items():
                setattr(self, param, value)
        else:
            self._invalid(serializer.errors)
