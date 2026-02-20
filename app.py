from spi_config import get_config
import os
from django.core.wsgi import get_wsgi_application


config = get_config()
os.environ["DJANGO_SETTINGS_MODULE"] = config["django"]["settings_module"]

app = get_wsgi_application()
