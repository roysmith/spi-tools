import os
from pathlib import Path
from django.core.wsgi import get_wsgi_application


os.environ['DJANGO_SECRET'] = (Path.home() / 'www/python/secret').read_text().strip()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tools_app.settings")
app = get_wsgi_application()
