from django import template
from django.utils.html import format_html

register = template.Library()


@register.filter
def highlight_search(value):
    """Render fixed headline markers while escaping every OCR-derived segment."""
    output = format_html("")
    remaining = str(value)
    while "[[[HIT]]]" in remaining:
        before, marked, remaining = remaining.partition("[[[HIT]]]")
        hit, separator, after = remaining.partition("[[[/HIT]]]")
        output = format_html("{}{}", output, before)
        if not separator:
            remaining = marked + remaining
            break
        output = format_html("{}<mark>{}</mark>", output, hit)
        remaining = after
    return format_html("{}{}", output, remaining)
