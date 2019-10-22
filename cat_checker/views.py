from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from mwclient import Site

from .forms import GetPageTitleForm

def index(request):
    context = {}
    return render(request, 'cat_checker/index.dtl', context)

@login_required()
def profile(request):
    context = {}
    return render(request, 'cat_checker/profile.dtl', context)

def login_oauth(request):
    context = {}
    return render(request, 'cat_checker/login.dtl', context)

def get_page_title(request):
    if request.method == 'POST':
        form = GetPageTitleForm(request.POST)
        if form.is_valid():
            page_title = form.cleaned_data['page_title']
            context = _find_supercategories(page_title)
            return render(request, 'cat_checker/page_title.dtl', context)
    else:
        form = GetPageTitleForm()
    context = {'form': form} 
    return render(request, 'cat_checker/get_page_title.dtl', context)

def _find_supercategories(page_title):
    """Return a context."""
    categories = _get_categories(page_title, 3)
    context = {
        'title': page_title,
        'categories': [c.name for c in categories],
    }
    return context
    

def _get_categories(page_title, depth):
    """Return a set of CategoryGraphs for the given page.
    The category graph will be navigated to the specified depth."""
    category_names = _get_category_names(page_title)
    categories = set()
    for name in category_names:
        g = CategoryGraph(name)
        if depth > 1:
            g.parents = _get_categories(name, depth-1)
        categories.add(g)
    return categories
            

def _get_category_names(page_title):
    """Return a set of the names of the categories this page belongs to."""
    ua = "CheckRefs/0.0 (User:RoySmith)"
    site = Site('en.wikipedia.org', clients_useragent=ua)
    page = site.pages[page_title].resolve_redirect()
    return {cat.name for cat in page.categories()}


class CategoryGraph:
    def __init__(self, name, parents=None):
        """Construct a CategoryGraph.  If parents is present, it should be
        an iterable over CategoryGraphs.
        """
        self.name = name
        if parents:
            self.parents = set(parents)
        else:
            self.parents = set()

    def __iter__(self):
        for parent in self.parents:
            yield parent

    def __eq__(self, other):
        return self.name == other.name and self.parents == other.parents

    def __hash__(self):
        # Hashing just the name is rather minimal, but simple, and
        # probably good enough for our purposes.
        return hash(self.name)

    def __str__(self):
        return('%s: %s' % (self.name, self.parents))

    def __repr__(self):
        return('%s: %s' % (self.name, self.parents))

    def flatten(self):
        """Return a set of all the category names in the graph.  This
        includes the current node, and recursively all of its parents."""
        names = {self.name}
        for parent in self.parents:
            names |= parent.flatten()
        return names

    def dfs(self, search_name, previous_path=None):
        """Find the node named search_name in the graph.  Returns
        the path to the node if found, None otherwise."""
        path = list(previous_path) if previous_path else []
        path.append(self.name)
        if search_name == self.name:
            return path
        for g in self.parents:
            found_path = g.dfs(search_name, path)
            if found_path:
                return found_path
        return None
