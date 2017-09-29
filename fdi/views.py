from fdi.models import Investments
from core.views import BaseMIView


class BaseFDIView(BaseMIView):

    queryset = Investments.objects.all()

    def get_queryset(self):
        return self.queryset
