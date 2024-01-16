# drfwn_quick

Handle full serialization of nested models quickly.

## Overview

`drfwn-quick` (django rest framework writable nested quick) extends `drf-writable-nested`
to allow nested models to be serialized rapidly with full data for relations
by taking advantage of django's `queryset.values()` method.

Example API response with `drfwn-quick`:
```
[
    {
        'id': 1,
        'name': 'Beans',
        'description': 'Some beans.',
        'enabled': False,
        'vendors': [
            {
                'id': 1,
                'name': 'Beans Emporium',
                'about': 'We sell beans.',
                'enabled': False
            }
        ]
    }
]
```

Example without:
```
[
    {
        'id': 1,
        'name': 'Beans',
        'description': 'Some beans.',
        'enabled': False,
        'vendors': [1]
    }
]
```

Note that without `drfwn-quick`, the relational field `"vendors"` is simply
a representation of database primary keys (IDs).

## Features

### Full Data

As seen in the overview above, responses with relations are looked-up to return
complete data from the API call, not just IDs (primary keys).

Note that so long as `DRFWN_QUICK_ALWAYS` is falsy, a url parameter is used to 
control this behaviour. This means that the original serialization can remain
accessible by default, for things such as the DRF UI, if desired.

### Performance

Data is built *quickly* by only accessing `queryset.values()` for the object and
it's relation's querysets. Because this does not instsntiate Model objects for each
value within the queryset(s), it is significantly faster on larger datasets.

#### Timed Examples

Coming... :)

### Writable

This is native to `drf-writable-nested` but because `drfwn-quick` extends it,
it's worth noting that the nested values are writable, and require only IDs
to do so.

However, note that a key difference between `drf-writable-nested` alone and 
`drfwn-quick` is that the response after ceating or updating a value can be
fully contextual, if quick is enabled for that call/always.

Meaning, a `POST` or `PUT` request may have a payload with `{..., "relation": [1, 3]}`
but still yield `{..., "relation": [{"id": 1, ...}, {"id": 3, ...}]}`.

## `settings.py`

There are a few items that can be set via the local Django app's `settings.py`
file.

| Setting | Default | About |
|---|---|---|
| `DRFWN_QUICK_ALWAYS` | `False` | If true, removed the need to pass a URL param to enable quick functionality. |
| `DRFWN_QUICK_DATETIME_FORMAT` | `"%Y/%m/%d"` | The format to use for `datetime.datetime` serialisation. |
| `DRFWN_QUICK_HANDLE_DATETIMES` | `True` | If true, serialise `datetime.datetime` objects. |
| `DRFWN_QUICK_URL_PAGE_PARAM_NAME` | `"page_size"` | The URL parameter name to use for page size. |
| `DRFWN_QUICK_URL_QUICK_PARAM_NAME` | `"quick"` | The URL parameter name to control quick functionality. |

## Tests

Tests exist, if you want to contribute, please consider tests. There's always
room for improvement on existing tests, too.

Coverage report will be added eventually.