from urllib.parse import urlsplit
from django.urls import reverse


def reader_return(value):
    """Only explicit local list routes can be reader return destinations."""
    routes = {reverse("home"): "Workspace", reverse("search"): "Workspace",
              reverse("resps"): "Search results", reverse("library"): "My library"}
    if value and len(value) <= 4096 and not any(ord(c) < 32 for c in value) and "\\" not in value:
        try:
            parsed = urlsplit(value)
            if not parsed.scheme and not parsed.netloc and value.startswith("/") and not value.startswith("//") and parsed.path in routes:
                return value, routes[parsed.path]
        except ValueError:
            pass
    return reverse("resps"), "Deep query"
