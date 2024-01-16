import datetime
import os
import unittest
from unittest.mock import MagicMock

import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
django.setup()

from drfwn_quick.data import rel_is_to_many, prepare_row, format_queryset_data
from drfwn_quick.settings import DATETIME_FORMAT


class TestData(unittest.TestCase):
    def test_rel_is_to_many(self) -> None:
        field = MagicMock()
        # Verify get expected bool based on field type.
        field.many_to_many = True
        field.one_to_many = False
        field.many_to_one = False
        field.one_to_one = False
        self.assertTrue(rel_is_to_many(field))
        field.many_to_many = False
        field.one_to_many = True
        field.many_to_one = False
        field.one_to_one = False
        self.assertTrue(rel_is_to_many(field))
        field.many_to_many = False
        field.one_to_many = False
        field.many_to_one = True
        field.one_to_one = False
        self.assertFalse(rel_is_to_many(field))
        field.many_to_many = False
        field.one_to_many = False
        field.many_to_one = False
        field.one_to_one = True
        self.assertFalse(rel_is_to_many(field))

    def test_prepare_row(self) -> None:
        # Ensure relations are expanded if "quick" and datetime.datetime
        # is serialised, if desired.
        related_datasets = {
            "related_field_a": {1: {"id": 1, "name": "panko"}},
            "related_field_b": {2: {"id": 2, "name": "breck"}},
        }
        # Set up a mock object with various types of fields.
        dataset_row = {
            "id": 6,
            "none_field": None,
            "true_bool_field": True,
            "false_bool_field": False,
            "datetime_field": datetime.datetime.now(),
            "other_field_str": "test",
            "other_field_int": 17,
            "other_field_dict": {"captain": "jack"},
            "other_field_list": ["will", "get", "you", "by", "tonight"],
            "related_field_a": 1,
            "related_field_b": 2,
        }
        related_field_names = ["related_field_a", "related_field_b"]
        # Ensure that NoneType, bools, ints are all unchanged.
        none_test = prepare_row(
            dataset_row,
            ["none_field"],
            related_field_names,
            related_datasets,
        )
        bool_test = prepare_row(
            dataset_row,
            ["true_bool_field", "false_bool_field"],
            related_field_names,
            related_datasets,
        )
        other_test = prepare_row(
            dataset_row,
            [
                "other_field_str",
                "other_field_int",
                "other_field_dict",
                "other_field_list"
            ],
            related_field_names,
            related_datasets,
        )
        unchanged_fields_tests = {
            "none_field": none_test,
            "true_bool_field": bool_test,
            "false_bool_field": bool_test,
            "other_field_str": other_test,
            "other_field_int": other_test,
            "other_field_dict": other_test,
            "other_field_list": other_test,
        }
        for key, test in unchanged_fields_tests.items():
            self.assertEqual(dataset_row[key], test[key])
        # TTest that datetime conversion occured with correct format.
        datetime_test = prepare_row(
            dataset_row,
            ["datetime_field"],
            related_field_names,
            related_datasets,
        )
        self.assertTrue(isinstance(datetime_test["datetime_field"], str))
        try:
            datetime.datetime.strptime(
                datetime_test["datetime_field"],
                DATETIME_FORMAT
            )
        except Exception:
            raise AssertionError(f"Datetime format mismatch: {DATETIME_FORMAT}")
        # Test that relations are full data.
        related_field_names_test = prepare_row(
            dataset_row,
            ["related_field_a", "related_field_b"],
            related_field_names,
            related_datasets,
        )
        for related_field_name in related_field_names:
            self.assertEqual(
                related_field_names_test[related_field_name],
                [
                    related_datasets[related_field_name][
                        dataset_row[related_field_name]
                    ]
                ],
            )

    def test_format_queryset_data(self) -> None:
        related_field_a = MagicMock()
        related_field_b = MagicMock()
        related_field_a.name = "related_field_a"
        related_field_b.name = "related_field_b"
        related_field_a.many_to_many = True
        related_field_b.many_to_many = True
        queryset = MagicMock()
        queryset.model = MagicMock()
        queryset.model._meta = MagicMock()
        related_datasets = {
            "related_field_a": {
                1: {"id": 1, "name": "beans"},
                2: {"id": 2, "name": "bacon"},
            },
            "related_field_b": {11: {"id": 11, "name": "eggs"}},
        }
        db_rows = [
            {"name": "Breakfast", "id": 1, "related_field_a": 1},
            {"name": "Breakfast", "id": 1, "related_field_a": 2},
            {"name": "Lunch", "id": 2, "related_field_b": 11},
        ]
        queryset.values = lambda *args: db_rows
        queryset.model._meta.get_fields = lambda: [
            related_field_a,
            related_field_b,
        ]
        field_names = ["name", "related_field_a", "related_field_b"]
        # Everything above is setup for below tests.
        formatted_data = format_queryset_data(
            field_names,
            queryset,
            related_datasets,
        )
        # Ensure that formatted data is a list of dicts.
        self.assertTrue(isinstance(formatted_data, list))
        self.assertTrue(all([isinstance(i, dict) for i in formatted_data]))
        # Ensure related data is full data.
        self.assertEqual(
            formatted_data[1]["related_field_b"],
            [
                related_datasets["related_field_b"][
                    formatted_data[1]["related_field_b"][0]["id"]
                ]
            ]
        )
