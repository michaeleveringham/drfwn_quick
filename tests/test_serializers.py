import os
import unittest
from unittest.mock import MagicMock, patch

import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
django.setup()

import drfwn_quick.serializers
from drfwn_quick.serializers import QuickableNestedModelSerializer


class TestQuickableNestedModelSerializer(unittest.TestCase):
    def test__init__(self) -> None:
        request = MagicMock()
        _serializer = QuickableNestedModelSerializer
        QuickableNestedModelSerializer.Meta = MagicMock()
        # Test that GET and determine_quick set self.quick, format is called.
        with (
            patch.object(drfwn_quick.serializers, "determine_quick", return_value=True),
            patch.object(drfwn_quick.serializers, "format_queryset_data") as mock_format,
        ):
            request.method = "GET"
            _serializer(context={"request": request})
            mock_format.assert_called()
        # Test that either not GET or determine_quick being False result in
        # not setting self.quick, format is not called.
        with patch.object(drfwn_quick.serializers, "format_queryset_data") as mock_format:
            with patch.object(drfwn_quick.serializers, "determine_quick", return_value=True):
                request.method = "POST"
                _serializer(context={"request": request})
                mock_format.assert_not_called()
            with patch.object(drfwn_quick.serializers, "determine_quick", return_value=False):
                request.method = "GET"
                _serializer(context={"request": request})
                mock_format.assert_not_called()
        # Test that force_quick ignores other qualifiers.
        with patch.object(drfwn_quick.serializers, "format_queryset_data") as mock_format:
            with patch.object(drfwn_quick.serializers, "determine_quick", return_value=False):
                request.method = "POST"
                _serializer(context={"request": request}, force_quick=True)
                mock_format.assert_called()
