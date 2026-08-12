from django.apps import AppConfig


class VideoContentAppConfig(AppConfig):
    name = 'video_content_app'

    def ready(self):
        from .services import signals
