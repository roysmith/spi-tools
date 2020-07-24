from django import template
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe


register = template.Library()


def safe(text, autoescape):
    if autoescape:
        return conditional_escape(text)
    else:
        return text


@register.filter(needs_autoescape=True)
def page_link(page_name, display_text=None, autoescape=True):
    """Return an anchor to a wiki page, similar to [[double brackets]].

    If display_text if truthy, it is used as the anchor display text.
    Otherwise, the display text defaults to the page_name.

    """
    pn = safe(page_name, autoescape)
    dt = safe(display_text or page_name, autoescape)
    return mark_safe(f'<a href="https://en.wikipedia.org/wiki/{pn}">{dt}</a>')


@register.filter(needs_autoescape=True)
def user_link(user_name, autoescape=True):
    """Return an anchor to a user page, similar to a {{u}} template.

    The displayed text is 'user_name', but the link is to 'User:user_name.'

    """
    un = safe(user_name, autoescape)
    return mark_safe(f'<a href="https://en.wikipedia.org/wiki/User:{un}">{un}</a>')

@register.filter(needs_autoescape=True)
def contributions(user_name, display_text=None, autoescape=True):
    """Return an anchor to a user's contributions.

    If display_text if truthy, it is used as the anchor display text.
    Otherwise, the display text defaults to 'contributions'.
    """
    un = safe(user_name, autoescape)
    dt = safe(display_text or 'contributions', autoescape)
    return mark_safe(f'<a href="https://en.wikipedia.org/wiki/Special:Contributions/{un}">{dt}</a>')

@register.filter(needs_autoescape=True)
def deleted_contributions(user_name, display_text=None, autoescape=True):
    """Return an anchor to a user's deleted contributions.

    If display_text if truthy, it is used as the anchor display text.
    Otherwise, the display text defaults to 'deleted contributions'.
    """
    un = safe(user_name, autoescape)
    dt = safe(display_text or 'deleted contributions', autoescape)
    return mark_safe(f'<a href="https://en.wikipedia.org/wiki/Special:DeletedContributions/{un}">{dt}</a>')
