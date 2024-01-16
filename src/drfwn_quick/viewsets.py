from django.core.exceptions import ImproperlyConfigured
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ListSerializer
from rest_framework.viewsets import ModelViewSet

from drfwn_quick.serializers import QuickableNestedModelSerializer
from drfwn_quick.settings import URL_PAGE_PARAM_NAME
from drfwn_quick.utils import determine_quick


class QuickPageNumberPagination(PageNumberPagination):
    page_size_query_param = URL_PAGE_PARAM_NAME


class QuickableNestedModelViewSet(ModelViewSet):
    """
    A viewset that permits modification of a model with nested values.

    Requires use of a QuickableNestedModelSerializer serializer as DRF will
    raise errors attempting to handled nested representations.
    """
    pagination_class = QuickPageNumberPagination

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        if (
            QuickableNestedModelSerializer
            not in self.serializer_class.__bases__
        ):
            raise ImproperlyConfigured(
                "QuickableNestedModelViewSet must use a"
                " QuickableNestedModelSerializer serializer."
            )

    def update(self, request: Request, *args, **kwargs) -> Response:
        """
        Slightly modified version of update that follows standard logic but
        if self.quick is set, instantiates a serializer forcing quick after
        update is finished, so that the returned data is detailed.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=partial,
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}
        data = serializer.data
        # Re-serializer data, forcing quick format, if given.
        if self.quick:
            data = serializer.__class__(
                instance=instance,
                data=data,
                force_quick=True,
            ).data
        return Response(data)

    def create(self, request: Request, *args, **kwargs) -> Response:
        """
        Slightly modified version of create that follows standard logic but
        if self.quick is set, instantiates a serializer forcing quick after
        create is finished, so that the returned data is detailed.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        data = serializer.data
        # Re-serializer data, forcing quick format, if given.
        if self.quick:
            data = serializer.__class__(
                instance=data["id"],
                data=data,
                force_quick=True,
            ).data
        return Response(data, status=status.HTTP_201_CREATED, headers=headers)

    def get_serializer(
        self,
        *args,
        **kwargs,
    ) -> ListSerializer | QuickableNestedModelSerializer:
        """
        Check if "many" is present in kwargs, if so and quick is being used,
        remove it. Otherwise, DRF will initialise ListSerializer instead.
        """
        if hasattr(self, "request") and hasattr(self.request, "query_params"):
            self.quick = determine_quick(self.request)
            # Set self.quick but only pop kwargs if GET request.
            if (
                self.quick
                and "many" in kwargs.keys()
                and self.request.method == "GET"
            ):
                kwargs.pop("many")
        return super().get_serializer(*args, **kwargs)
