import json
import warnings

from rest_framework.request import Request

from drfwn_quick.settings import ALWAYS_QUICK, URL_QUICK_PARAM_NAME


def determine_quick(request: Request) -> bool:
    url_arg = request.query_params.get(URL_QUICK_PARAM_NAME, "false").lower()
    try:
        url_arg_loaded = json.loads(url_arg)
    except Exception:
        warnings.warn(
            f"Failed to JSON load url arg {URL_QUICK_PARAM_NAME}: {url_arg}"
        )
        url_arg_loaded = False
    if ALWAYS_QUICK or url_arg_loaded:
        return True
    else:
        return False
