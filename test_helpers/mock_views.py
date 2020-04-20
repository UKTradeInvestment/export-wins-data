from django.utils.decorators import decorator_from_middleware
from rest_framework.response import Response
from rest_framework.views import APIView

from alice.middleware import alice_exempt
from core.hawk import HawkAuthentication, HawkResponseMiddleware, HawkScopePermission
from core.types import HawkScope
from django.utils.decorators import method_decorator


@method_decorator(alice_exempt, name='dispatch')
class HawkViewWithoutScope(APIView):
    """View using Hawk authentication."""

    authentication_classes = (HawkAuthentication,)

    @decorator_from_middleware(HawkResponseMiddleware)
    def get(self, request):
        """Simple test view with fixed response."""
        return Response({'content': 'hawk-test-view-without-scope'})


@method_decorator(alice_exempt, name='dispatch')
class HawkViewWithScope(APIView):
    """View using Hawk authentication."""

    authentication_classes = (HawkAuthentication,)
    permission_classes = (HawkScopePermission,)
    required_hawk_scope = next(iter(HawkScope.__members__.values()))

    @decorator_from_middleware(HawkResponseMiddleware)
    def get(self, request):
        """Simple test view with fixed response."""
        return Response({'content': 'hawk-test-view-with-scope'})
