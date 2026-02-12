from config import get_config
import os
from django.core.wsgi import get_wsgi_application


config = get_config()
os.environ["DJANGO_SETTINGS_MODULE"] = config["django"]["settings_module"]
os.environ["DJANGO_SECRET"] = config["django"]["secret"]
os.environ["MEDIAWIKI_KEY"] = config["oauth"]["mediawiki_key"]
os.environ["MEDIAWIKI_SECRET"] = config["oauth"]["mediawiki_secret"]
os.environ["MEDIAWIKI_URL"] = config["oauth"]["mediawiki_url"]
os.environ["MEDIAWIKI_CALLBACK"] = config["oauth"]["mediawiki_callback"]

app = get_wsgi_application()
