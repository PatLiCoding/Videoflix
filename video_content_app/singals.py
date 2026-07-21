from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
import os

from .models import Video


@receiver(post_save, sender=Video)
def video_post_save(sender, instance, created, **kwargs):
    print('Video saved')
    if created:
        print('New Video created')


@receiver(post_delete, sender=Video)
def auto_delete_video_file_on_delete(sender, instance, **kwargs):
    if instance.video_file:
        if os.path.isfile(instance.video_file.path):
            os.remove(instance.video_file.path)
