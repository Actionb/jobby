from django import template
from django.utils.http import urlencode

from jobby.views import PAGE_VAR

register = template.Library()


@register.simple_tag(takes_context=True)
def paginator_url(context, page_number):
    params = dict(context["request"].GET.items())
    params[PAGE_VAR] = page_number
    return "?%s" % urlencode(sorted(params.items()))
