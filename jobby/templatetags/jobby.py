from urllib.parse import parse_qsl, unquote, urlparse, urlunparse

from django import template
from django.urls import Resolver404, get_script_prefix, resolve
from django.utils.http import urlencode

register = template.Library()


@register.simple_tag(takes_context=True)
def paginator_url(context, page_number):
    from jobby.views import PAGE_VAR  # avoid circular import

    params = dict(context["request"].GET.items())
    params[PAGE_VAR] = page_number
    return "?%s" % urlencode(sorted(params.items()))


@register.simple_tag(takes_context=True)
def add_search_filters(context, url):
    """
    Add the preserved search form parameters to the given url.

    When navigating away from a search page, the search parameters will be
     added to the query string like this: '_search_filters=was%3DFoo%26wo%3DBar'

    When navigating back to the search page, the filters are recovered from the
    above query string parameter:
        '_search_filters=was%3DFoo%26wo%3DBar' => 'was=Foo&wo=Bar'
    """
    search_filters = context.get("preserved_search_filters")

    parsed_url = list(urlparse(url))
    parsed_qs = parse_qsl(parsed_url[4])
    merged_qs = []

    if search_filters:
        # Check if the url is for a search page. If it is, parse the preserved
        # filters and extract the search filters parameters, so that they
        # can be added to the query string. For example:
        #  search_filters is:         '_search_filters=was%3DFoo%26wo%3DBar'
        #  search_filters should be:  'was=Foo&wo=Bar'
        search_filters = parse_qsl(search_filters)  # [('_search_filters', 'was=Foo&wo=Bar')]
        match_url = f"/{unquote(url).partition(get_script_prefix())[2]}"
        try:
            match = resolve(match_url)
        except Resolver404:  # pragma: no cover
            pass
        else:
            filters = dict(search_filters).get("_search_filters")
            if match.url_name == "suche" and filters:
                search_filters = parse_qsl(filters)  # [('was', 'Foo'), ('wo', 'Bar')]

        merged_qs.extend(search_filters)

    merged_qs.extend(parsed_qs)

    parsed_url[4] = urlencode(merged_qs)
    return urlunparse(parsed_url)
