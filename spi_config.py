import configparser
import os

def get_config():
    """Read and parse the application's config file.

    Cryptographic (i.e. secret) keys are in the config file, so it
    must have secure file system permissions.
    """
    
    config = configparser.ConfigParser()
    config.read(os.environ["SPI_TOOLS_CONFIG_FILE"])
    return config
