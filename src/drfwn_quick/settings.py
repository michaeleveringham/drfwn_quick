from django.conf import settings


ALWAYS_QUICK = getattr(settings, "DRFWN_QUICK_ALWAYS", False)

DATETIME_FORMAT = getattr(settings, "DRFWN_QUICK_DATETIME_FORMAT", "%Y/%m/%d")
HANDLE_DATETIMES = getattr(settings, "DRFWN_QUICK_HANDLE_DATETIMES", True)

URL_PAGE_PARAM_NAME = getattr(
    settings,
    "DRFWN_QUICK_URL_PAGE_PARAM_NAME",
    "page_size",
)
URL_QUICK_PARAM_NAME = getattr(
    settings,
    "DRFWN_QUICK_URL_QUICK_PARAM_NAME",
    "quick",
)
