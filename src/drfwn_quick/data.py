import datetime
from typing import Any

from django.db.models.fields import Field
from django.db.models.query import QuerySet

from drfwn_quick.settings import DATETIME_FORMAT, HANDLE_DATETIMES


DATASET = dict[int, dict[str, Any]]


def rel_is_to_many(field: Field) -> bool:
    """Check if a relation is either (many/one)-to-many or (many/one)-to-one."""
    if field.many_to_many or field.one_to_many:
        return True
    elif field.many_to_one or field.one_to_one:
        return False


def prepare_row(
    dataset_row: dict[str, Any],
    field_names: list[str],
    rel_names: list[str],
    datasets: dict[str, DATASET],
) -> dict[str, Any]:
    """
    Prepare a row to be added into API response data.

    This method does not actual jsonify the data in the row (except for
    datetime.datetime, if settings.DRFWN_QUICK_HANDLE_DATETIMES is true).
    Instead, this looks up related rows by relation ID and replaces it in
    the return dict.
    """
    row = {"id": dataset_row["id"]}
    for field_name in field_names:
        item = dataset_row.get(field_name, None)
        # Relations are to-many fields, empty values need to be empty lists.
        if item is None:
            value = None if field_name not in rel_names else []
        elif field_name in rel_names:
            related_row = datasets[field_name][item]
            if not HANDLE_DATETIMES:
                value = related_row
            else:
                value = {
                    k: v.strftime(DATETIME_FORMAT)
                    if isinstance(v, datetime.datetime)
                    else v
                    for k, v in related_row.items()
                }
            # Needs to be list for later concatenation, if required.
            value = [value]
        elif HANDLE_DATETIMES and isinstance(item, datetime.datetime):
            value = item.strftime(DATETIME_FORMAT)
        else:
            value = item
        row[field_name] = value
    return row


def format_queryset_data(
    field_names: list[str],
    queryset: QuerySet,
    related_datasets: dict[str, DATASET],
) -> list[dict[str, Any]]:
    """
    Ensure a queryset's data is formatted correctly, replacing relation IDs
    with real values.
    """
    rel_names = [
        f.name for f in queryset.model._meta.get_fields() if rel_is_to_many(f)
    ]
    # Much faster to use queryset.values() instead of queryset iteration.
    dataset_rows = list(queryset.values(*field_names, "id"))
    formatted_rows = {}
    ids_to_merge = set()
    for dataset_row in dataset_rows:
        row_id = dataset_row["id"]
        formatted_row = prepare_row(
            dataset_row,
            field_names,
            rel_names,
            related_datasets,
        )
        if row_id not in formatted_rows.keys():
            formatted_rows[row_id] = formatted_row
        else:
            ids_to_merge.add(row_id)
            for rel_name in rel_names:
                existing_row = formatted_rows[row_id]
                if rel_name in existing_row.keys():
                    old_val = existing_row[rel_name]
                    new_val = formatted_row[rel_name]
                    if new_val:
                        formatted_rows[row_id][rel_name] = old_val + new_val
    return list(formatted_rows.values())
