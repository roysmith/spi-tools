import configparser
import os
from pathlib import Path
from django.core.wsgi import get_wsgi_application

def get_config(ini_path):
    ini_mode = os.stat(ini_path).st_mode
    if ini_mode & 0o77:
        raise RuntimeError("%s has mode %o,: access by non-owner disallowed" %
                           (ini_path, ini_mode))
    config = configparser.ConfigParser()
    config.read(ini_path)
    return config

config_dir = Path.home() / "www/python"

config = get_config(str(config_dir / "config.ini"))

os.environ.setdefault("MEDIAWIKI_KEY", config["oauth"]["mediawiki_key"])
os.environ.setdefault("MEDIAWIKI_SECRET", config["oauth"]["mediawiki_secret"])
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tools_app.settings")
os.environ.setdefault("DJANGO_SECRET", config["django"]["django_secret"])


app = get_wsgi_application()
