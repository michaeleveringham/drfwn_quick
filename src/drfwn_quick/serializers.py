import warnings
from typing import Any

from django.db.models import Model
from django.db.models.fields import Field
from drf_writable_nested import WritableNestedModelSerializer
from rest_framework.fields import empty
from rest_framework.utils.serializer_helpers import ReturnDict

from drfwn_quick.data import format_queryset_data
from drfwn_quick.utils import determine_quick


class QuickableNestedModelSerializer(WritableNestedModelSerializer):
    def __init__(
        self,
        instance: list[Model] | int | None = None,
        data: dict | empty = empty,
        force_quick: bool = False,
        **kwargs,
    ) -> None:
        request = kwargs.get("context", {}).get("request", None)
        self.quick = force_quick or (
            determine_quick(request)
            # Only use quick on GET unless forced.
            and request.method == "GET"
        )
        if self.quick:
            field_names = [
                f.name for f in self.Meta.model._meta.get_fields()
                if isinstance(f, Field)
            ]
            self._ensure_related_querysets()
            related_datasets = {
                k: {i["id"]: i for i in qs.values()}
                for k, qs in self.related_querysets.items()
            }
            if not hasattr(self, "queryset"):
                warnings.warn(
                    f"Queryset not defined for model {self.Meta.model}"
                    f" in serializer {self.__class__}. Setting it now"
                    " for this request, define it in the serializer to"
                    " increase performance."
                )
                self.queryset = self.Meta.model.objects.all()
            queryset = self.queryset
            # If given an instance, filter by IDs.
            if instance:
                if type(instance) is int:
                    ids = [instance]
                else:
                    try:
                        ids = [instance.id]
                    except AttributeError:
                        ids = [i.id for i in instance]
                queryset = queryset.filter(id__in=ids)
            data = format_queryset_data(field_names, queryset, related_datasets)
        super().__init__(instance, data, **kwargs)
        if data is not empty:
            self.is_valid()
        self._quick_data = data

    def _ensure_related_querysets(self) -> None:
        """Check if related querysets are defined, if not, set them."""
        self.related_querysets = getattr(self, "related_querysets", {})
        rels = {
            f.name: f.related_model for f in self.Meta.model._meta.get_fields()
            if f.is_relation
        }
        for rel_name, rel_model in rels.items():
            if rel_name not in self.related_querysets.keys():
                warnings.warn(
                    f"Relation \"{rel_name}\" in serializer"
                    f" {self.__class__} for {self.Meta.model}"
                    " is not defined in the serializer's related_querysets."
                    " Setting it now for this request, define it in the"
                    " serializer to increase performance."
                )
                self.related_querysets[rel_name] = rel_model.objects.all()

    @property
    def data(self) -> list[dict[str, Any]] | ReturnDict:
        if self.quick:
            return self._quick_data
        else:
            return super().data
