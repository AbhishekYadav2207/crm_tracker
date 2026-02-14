from django.apps import AppConfig

class ChcConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chc'

    def ready(self):
        import chc.signals
