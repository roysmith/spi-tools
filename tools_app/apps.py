import logging
from django.apps import AppConfig


logger = logging.getLogger('app')


class ToolsAppConfig(AppConfig):
    name = 'tools_app'

    def ready(self):
        logger.critical(f'{self.name} starting')
