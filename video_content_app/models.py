from django.db import models

# Create your models here.


class Video(models.Model):
    """Represents an uploaded video and its metadata.

    A Video is created with just an original ``video_file``; a
    post_save signal then queues an asynchronous RQ job that
    converts the source file into HLS renditions (480p/720p/1080p)
    stored under ``media/videos/hls/<id>/<resolution>/``. The title
    defaults to "Generating..." to reflect that processing may not
    be finished yet when the record is first created.
    """

    VIDEO_CATEGORY = [
        ('action', 'Action'),
        ('anime', 'Anime'),
        ('comedies', 'Comedies'),
        ('crime', 'Crime'),
        ('documentaries', 'Documentaries'),
        ('drama', 'Drama'),
        ('fantasy', 'Fantasy'),
        ('horror', 'Horror'),
        ('kids_family', 'Kids & Family'),
        ('romance', 'Romance'),
        ('sci_fi', 'Sci-Fi'),
        ('thrillers', 'Thrillers'),
    ]

    created_at = models.DateTimeField(auto_now_add=True)
    title = models.CharField(
        max_length=255, blank=True, default="Generating...")
    description = models.TextField(blank=True)
    thumbnail = models.ImageField(
        upload_to='thumbnails/', blank=True, null=True)
    category = models.CharField(
        max_length=20, choices=VIDEO_CATEGORY, default='action')
    video_file = models.FileField(
        upload_to="videos/originals/", blank=True, null=True)

    class Meta:
        """Meta options for the Video model."""
        ordering = ["-created_at"]
        verbose_name = "Video"
        verbose_name_plural = "Videos"

    def __str__(self):
        """
        Returns a string representation of the Video.

        Returns:
            str: The title of the video.
        """
        return self.title
