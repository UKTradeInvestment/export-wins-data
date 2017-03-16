import rest_framework
from rest_framework.decorators import list_route
from rest_framework.metadata import SimpleMetadata
from rest_framework.relations import RelatedField
from rest_framework.response import Response

from .authenticators import AlicePermission

# avoid foreign key lookups for choices - getting metadata causes N queries
# where N is number of foreign keys!
# don't have time to upgrade DRF for this so just hack it in
# https://github.com/tomchristie/django-rest-framework/issues/3751
# to back out just reverse this commit
if rest_framework.__version__ != '3.3.3':
    raise Exception('DRF updated, remove hack plz')


class NoRelatedFieldChoicesMetadata(SimpleMetadata):
    def get_field_info(self, field):
        related_field = isinstance(field, RelatedField)
        if related_field:
            # prevent querying related field
            field.queryset = field.queryset.none()
        field_info = super().get_field_info(field)
        if related_field:
            # don't need choices now
            field_info.pop('choices')
        return field_info


class AliceMixin(object):
    """
    Mixin for ViewSets used by Alice clients which authenticate via Alice and
    reflect on schema view.
    """

    metadata_class = NoRelatedFieldChoicesMetadata
    permission_classes = (AlicePermission,)

    @list_route(methods=("get",))
    def schema(self, request):
        """ Return metadata about fields of View's serializer """

        serializer = self.get_serializer()
        metadata_class = self.metadata_class()
        serializer_metadata = metadata_class.get_serializer_info(serializer)
        return Response(serializer_metadata)
