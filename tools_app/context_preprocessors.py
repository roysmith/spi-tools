from django.conf import settings

def get_from_settings(request):
    return {'VERSION_ID': settings.VERSION_ID}
