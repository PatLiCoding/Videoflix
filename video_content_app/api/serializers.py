from rest_framework import serializers

from video_content_app.models import Video


class VideoSerializer(serializers.ModelSerializer):
    """Serializes Video instances for the video list API endpoint.

    Exposes the thumbnail under the ``thumbnail_url`` key (read-only)
    by mapping it to the model's ``thumbnail`` ImageField via
    ``source``, so DRF returns the file's absolute/relative URL
    rather than accepting uploads through this field.
    """
    thumbnail_url = serializers.ImageField(source='thumbnail', read_only=True)

    class Meta:
        """Defines which model and fields this serializer exposes."""
        model = Video
        fields = ['id', 'created_at', 'title',
                  'description', 'thumbnail_url', 'category']
