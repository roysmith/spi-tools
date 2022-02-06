import logging

from django.conf import settings
from django.shortcuts import render, redirect
from django.views import View
from opensearchpy import OpenSearch


from search.forms import SearchForm

logger = logging.getLogger('search.views')


class IndexView(View):
    def get(self, request):
        form = SearchForm()
        context = {'form': form,
                   }
        return render(request, 'search/index.html', context)


    def post(self, request):
        form = SearchForm(request.POST)
        context = {'form': form,
                   }
        if form.is_valid():
            search_terms = form.cleaned_data['search_terms']
            auth=(settings.ELASTICSEARCH['user'], settings.ELASTICSEARCH['password'])
            es = OpenSearch(settings.ELASTICSEARCH['server'],
                            http_auth=auth)
            query = {
                "query": {
                    "bool": {
                        "must": [
                            {"match": {"comment": search_terms}}
                        ]
                    }
                }
            }
            es_results = es.search(body=query, index=settings.ELASTICSEARCH['index'])
            results = []
            for hit in es_results['hits']['hits']:
                r = {'page_id': hit['_source']['page_id'],
                     'rev_id': hit['_source']['rev_id'],
                     }
                results.append(r)
            context['results'] = results
            return render(request, 'search/results.html', context)

        return render(request, 'search/index.html', context)
