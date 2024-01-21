# drfwn_quick

Handle full serialization of nested models quickly.

## Installation

Install via PyPI, `pip install drfwn-quick`.

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

#### Timed Example

Bottomline: using **drfwn_quick served 31,000 related database entries, with full
context, in almost half the time.**

Read on for details on how this test was done.

Setup 2 identical Django apps, one using `drfwn_quick` and one not.

`models.py`
```python
from django.db import models


class Vendor(models.Model):
    name = models.CharField(max_length=256)
    about = models.TextField(blank=True, default='')
    enabled = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=256)
    description = models.TextField(blank=True, default='')
    enabled = models.BooleanField(default=False)
    vendors = models.ManyToManyField(Vendor, blank=True)

    def __str__(self):
        return self.name
```

`viewsets.py`
```python
from drfwn_quick.viewsets import QuickableNestedModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from apps.shopping.models import Vendor, Product, PurchaseRecord
from apps.shopping.serializers import VendorSerializer, ProductSerializer


class VendorViewSet(ModelViewSet):
    queryset = Vendor.objects.all().order_by("name")
    serializer_class = VendorSerializer
    permission_classes = [IsAuthenticated,]

# Replace base with QuickableNestedModelViewSet to enable.
#class ProductViewSet(QuickableNestedModelViewSet):
class ProductViewSet(ModelViewSet):
    queryset = Product.objects.all().order_by("-id")
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated,]
```

`serializers.py`
```python
from drf_writable_nested import WritableNestedModelSerializer
from drfwn_quick.serializers import QuickableNestedModelSerializer
from rest_framework.serializers import ModelSerializer

from apps.shopping.models import Vendor, Product


class VendorSerializer(ModelSerializer):
    class Meta:
        model = Vendor
        fields = "__all__"


# Replace base with QuickableNestedModelSerializer to enable.
#class ProductSerializer(QuickableNestedModelSerializer):
class ProductSerializer(WritableNestedModelSerializer):
    customers = VendorSerializer(many=True, required=False, allow_null=True)

    class Meta:
        model = Product
        fields = "__all__"
```

Using `Faker` 1,000 unique vendors and 31,000 unique products with up to 10
random vendors were inserted into the database.

The following tests were run:

```python
import timeit
import requests


elapsed = timeit.timeit(
    lambda: requests.get(
        # Non drfwn-quick enabled API.
        "http://127.0.0.1:8000/api/v0/product/",
        # URL, once enabled.
        #"http://127.0.0.1:8000/api/v0/product/?quick=true",
        headers={"Authorization": "Token <token>"},
    ),
    number=20,
)
print(elapsed)
```

This resulted in `2.2215011` for the non-enabled test and `1.1878105` when enabled,
about 46% faster!

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