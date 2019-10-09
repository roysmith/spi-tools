from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from mwclient import Site

from .forms import GetPageTitleForm

def index(request):
    context = {}
    return render(request, 'user_profile/index.dtl', context)

@login_required()
def profile(request):
    context = {}
    return render(request, 'user_profile/profile.dtl', context)

def login_oauth(request):
    context = {}
    return render(request, 'user_profile/login.dtl', context)

def get_page_title(request):
    if request.method == 'POST':
        form = GetPageTitleForm(request.POST)
        if form.is_valid():
            page_title = form.cleaned_data['page_title']
            categories = _get_category_tree(page_title, 3)
            context = {'title': page_title, 'categories': categories}
            return render(request, 'user_profile/page_title.dtl', context)
    else:
        form = GetPageTitleForm()
    context = {'form': form} 
    return render(request, 'user_profile/get_page_title.dtl', context)


def _get_category_tree(page_title, depth):
    categories = _get_page_categories(page_title)
    subcats = set()
    if depth > 1:
        for cat in categories:
            subcats.update(_get_category_tree(cat, depth-1))
    return categories | subcats
            
    

def _get_page_categories(page_title):
    """Return a set of the names of the categories this page belongs to."""
    ua = "CheckRefs/0.0 (User:RoySmith)"
    site = Site('en.wikipedia.org', clients_useragent=ua)
    page = site.pages[page_title].resolve_redirect()
    return {cat.name for cat in page.categories()}
