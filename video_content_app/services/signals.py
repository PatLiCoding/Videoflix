from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
import os
import django_rq

from video_content_app.models import Video
from video_content_app.services.tasks import convert_all_resolutions


@receiver(post_save, sender=Video)
def video_post_save(sender, instance, created, **kwargs):
    """Queue asynchronous HLS conversion for newly created videos.

    Runs after a Video row is saved. Only fires on creation (not on
    subsequent updates) and enqueues the conversion job on the
    default django-rq queue instead of running ffmpeg synchronously,
    so the request/response cycle isn't blocked by transcoding.

    Args:
        sender: The model class (Video).
        instance: The Video instance that was saved.
        created (bool): True if this save created a new row.
        **kwargs: Additional signal arguments (unused).
    """
    if created:
        queue = django_rq.get_queue('default')
        queue.enqueue(convert_all_resolutions, instance.id)


@receiver(post_delete, sender=Video)
def auto_delete_video_file_on_delete(sender, instance, **kwargs):
    """Remove the original video file from disk when its Video row is deleted.

    Django does not delete files referenced by FileField/ImageField
    automatically, so this cleans up the source file under
    ``videos/originals/`` to avoid orphaned uploads. Note: this only
    removes the original file, not the generated HLS renditions.

    Args:
        sender: The model class (Video).
        instance: The Video instance that was deleted.
        **kwargs: Additional signal arguments (unused).
    """
    if instance.video_file:
        if os.path.isfile(instance.video_file.path):
            os.remove(instance.video_file.path)
