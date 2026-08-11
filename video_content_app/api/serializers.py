from rest_framework import serializers

from video_content_app.models import Video


class VideoSerializer(serializers.ModelSerializer):
    thumbnail_url = serializers.ImageField(source='thumbnail', read_only=True)

    class Meta:
        model = Video
        fields = ['id', 'created_at', 'title',
                  'description', 'thumbnail_url', 'category']
