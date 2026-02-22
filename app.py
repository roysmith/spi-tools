from spi_config import get_config
import os
from django.core.wsgi import get_wsgi_application


config = get_config()
os.environ["DJANGO_SETTINGS_MODULE"] = "tools_app.settings"

app = get_wsgi_application()
