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
            OPENSEARCH = settings.OPENSEARCH
            client = OpenSearch(f'{OPENSEARCH["host"]}:{OPENSEARCH["port"]}',
                                http_auth=(OPENSEARCH['user'], OPENSEARCH['password']),
                                use_ssl=True,
                                verify_certs=False,
                                ssl_show_warn=False,
                                )
            query = {
                'query': {
                    'query_string': {
                        'query': 'co:added un:bear',
                    }
                }
            }
            os_results = client.search(body=query, index=OPENSEARCH['index'])
            results = []
            for hit in os_results['hits']['hits']:
                r = hit['_source']
                results.append(r)
            context['results'] = results
            return render(request, 'search/results.html', context)

        return render(request, 'search/index.html', context)
