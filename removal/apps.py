from django.apps import AppConfig


class RemovalConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'removal'

    def ready(self):
        import removal.signals 