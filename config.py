import configparser
import os
from pathlib import Path

def get_config():
    """Read and parse the application's config file.

    Cryptographic (i.e. secret) keys are in the config file, so enforce that it
    must have secure file system permissions.
    """
    ini_path = os.environ.get("SPI_TOOLS_CONGIG_FILE",
                              (Path.home() / "www/python/config.ini").as_posix())

    ini_mode = os.stat(ini_path).st_mode
    if ini_mode & 0o77:
        raise RuntimeError("%s has mode %o: access by non-owner disallowed" %
                           (ini_path, ini_mode))
    config = configparser.ConfigParser()
    config.read(ini_path)
    return config
