import os
from pathlib import Path
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tools_app.settings")
os.environ.setdefault("DJANGO_SECRET", (Path.home() / "www/python/secret").read_text().strip())

app = get_wsgi_application()
