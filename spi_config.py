import tomllib
import os
from pathlib import Path

def get_config() -> dict:
    """Read and parse the application's config file.

    Cryptographic (i.e. secret) keys are in the config file, so it
    should have secure file system permissions (i.e. not readable
    except by the owner).
    """
    config_path = os.environ.get("SPI_TOOLS_CONFIG_FILE",
                              (Path.home() / "www/python/config.toml").as_posix())

    config_file = open(config_path, 'rb')
    return tomllib.load(config_file)
