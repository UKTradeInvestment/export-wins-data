import logging

from django.utils.decorators import (
    decorator_from_middleware,
    method_decorator,
)

from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from alice.middleware import alice_exempt
from core.hawk import HawkAuthentication, HawkResponseMiddleware, HawkScopePermission
from core.types import HawkScope

logger = logging.getLogger(__name__)


@method_decorator(alice_exempt, name='dispatch')
class ActivityStreamViewSet(ViewSet):
    """List-only view set for the activity stream"""

    authentication_classes = (HawkAuthentication,)
    permission_classes = (HawkScopePermission,)
    required_hawk_scope = HawkScope.activity_stream

    @decorator_from_middleware(HawkResponseMiddleware)
    def list(self, request):
        """A single page of activities"""
        return Response({'secret': 'content-for-pen-test'})
