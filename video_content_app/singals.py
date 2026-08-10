from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
import os
import django_rq

from .models import Video
from .tasks import convert_all_resolutions


@receiver(post_save, sender=Video)
def video_post_save(sender, instance, created, **kwargs):
    if created:
        queue = django_rq.get_queue('default')
        queue.enqueue(convert_all_resolutions, instance.id)


@receiver(post_delete, sender=Video)
def auto_delete_video_file_on_delete(sender, instance, **kwargs):
    if instance.video_file:
        if os.path.isfile(instance.video_file.path):
            os.remove(instance.video_file.path)
