from django.apps import AppConfig


class VideoContentAppConfig(AppConfig):
    """Application configuration for video_content_app.

    Registers the app's Django signal handlers on startup so that
    video creation and deletion automatically trigger HLS conversion
    and file cleanup respectively.
    """
    name = 'video_content_app'

    def ready(self):
        """Import the signals module to connect its receivers.

        Django calls this once the app registry is fully populated.
        Importing services.signals here (rather than at module load
        time) ensures the post_save/post_delete receivers on Video
        are registered exactly once, without risking circular imports.
        """
        from .services import signals
