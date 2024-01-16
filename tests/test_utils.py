import os
import unittest
from unittest.mock import MagicMock, patch

import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
django.setup()

import drfwn_quick.utils
from drfwn_quick.settings import URL_QUICK_PARAM_NAME
from drfwn_quick.utils import determine_quick


class TestUtils(unittest.TestCase):
    def test_determine_quick(self) -> None:
        request = MagicMock()
        request.query_params = {URL_QUICK_PARAM_NAME: MagicMock()}
        # Test bad jsonifiable URL param.
        with self.assertWarns(Warning):
            self.assertFalse(determine_quick(request))
        # Test ALWAYS_QUICK or url param gives True.
        request.query_params = {URL_QUICK_PARAM_NAME: "true"}
        with patch.object(drfwn_quick.utils, "ALWAYS_QUICK", False):
            self.assertTrue(determine_quick(request))
        request.query_params = {URL_QUICK_PARAM_NAME: "false"}
        with patch.object(drfwn_quick.utils, "ALWAYS_QUICK", True):
            self.assertTrue(determine_quick(request))
        # Test neither gives False.
        with patch.object(drfwn_quick.utils, "ALWAYS_QUICK", False):
            self.assertFalse(determine_quick(request))
