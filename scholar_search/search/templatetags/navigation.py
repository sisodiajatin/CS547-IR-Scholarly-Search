from urllib.parse import urlencode
from django import template
from django.urls import reverse
from search.navigation import reader_return

register = template.Library()


@register.simple_tag(takes_context=True)
def reader_url(context, paper):
    request = context["request"]
    url = reverse("paper_detail", args=[paper.pk])
    if request.resolver_match.url_name == "paper_detail":
        origin = request.GET.get("return_to")
        if not origin:
            return url
    else:
        origin = request.get_full_path()
    origin, _ = reader_return(origin)
    return url + "?" + urlencode({"return_to": origin})
