"""
Not certain why but if this test case runs after others, it may fail.
Needs more investigation, for now, naming this test__viewsets.py.
"""
import os
import unittest
from unittest.mock import MagicMock, patch

import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
django.setup()
from django.core.exceptions import ImproperlyConfigured
from rest_framework.serializers import ListSerializer

import drfwn_quick.viewsets
from drfwn_quick.settings import URL_QUICK_PARAM_NAME
from drfwn_quick.serializers import QuickableNestedModelSerializer
from drfwn_quick.viewsets import QuickableNestedModelViewSet


class ChildQuickableNestedModelSerializer(QuickableNestedModelSerializer):
    """A bogus class used for tests since the base is abstract."""
    pass


class TestQuickableNestedModelViewSet(unittest.TestCase):
    def test__init__(self, **kwargs) -> None:
        # Test that InvalidConfiguration is raised if self.serializer
        # is not QuickableNestedModelSerializer.
        with self.assertRaises(ImproperlyConfigured):
            mock_serializer_class = MagicMock()
            mock_serializer_class.__bases__ = []
            with patch.object(
                QuickableNestedModelViewSet,
                "serializer_class",
                new=mock_serializer_class
            ):
                QuickableNestedModelViewSet()

    def test_update(self) -> None:
        mock_serializer = MagicMock()
        mock_serializer.__class__ = MagicMock()
        _vset = QuickableNestedModelViewSet
        with (
            patch.object(_vset, "__init__", return_value=None),
            patch.object(_vset, "get_object"),
            patch.object(_vset, "get_serializer", return_value=mock_serializer),
            patch.object(_vset, "perform_update"),
            patch.object(drfwn_quick.viewsets, "Response"),
        ):
            viewset = _vset()
            # Verifying that when quick is set, a new instance of the
            # serializer is spawned, and if not, it isn't.
            viewset.quick = False
            viewset.update(MagicMock())
            mock_serializer.__class__.assert_not_called()
            viewset.quick = True
            viewset.update(MagicMock())
            mock_serializer.__class__.assert_called_once()

    def test_create(self) -> None:
        mock_serializer = MagicMock()
        mock_serializer.__class__ = MagicMock()
        _vset = QuickableNestedModelViewSet
        with (
            patch.object(_vset, "__init__", return_value=None),
            patch.object(_vset, "get_serializer", return_value=mock_serializer),
            patch.object(_vset, "perform_create"),
            patch.object(_vset, "get_success_headers"),
            patch.object(drfwn_quick.viewsets, "Response"),
        ):
            viewset = _vset()
            # Similar to create, check that when quick is set, a new instance
            # of the serializer is spawned, and if not, it isn't.
            viewset.quick = False
            viewset.create(MagicMock())
            mock_serializer.__class__.assert_not_called()
            viewset.quick = True
            viewset.create(MagicMock())
            mock_serializer.__class__.assert_called_once()

    def test_get_serializer(self) -> None:
        request = MagicMock()
        request.method = "GET"
        serializer_class = ChildQuickableNestedModelSerializer
        nested_viewset = QuickableNestedModelViewSet(
            serializer_class=serializer_class,
            request=request,
        )
        nested_viewset.format_kwarg = (None,)
        # A ListSerializer is instantiated by drf by default; this is desired
        # when quick is not enabled.
        with patch.object(
            drfwn_quick.viewsets,
            "determine_quick",
            return_value=False,
        ):
            serializer = nested_viewset.get_serializer(many=True)
            self.assertTrue(isinstance(serializer, ListSerializer))
        # Ensure the actual serializer is used when quick is enabled.
        with patch.object(
            drfwn_quick.viewsets,
            "determine_quick",
            return_value=True,
        ):
            ChildQuickableNestedModelSerializer.Meta = MagicMock()
            request.query_params = {URL_QUICK_PARAM_NAME: "true"}
            serializer = nested_viewset.get_serializer(many=True)
            self.assertTrue(isinstance(serializer, serializer_class))
