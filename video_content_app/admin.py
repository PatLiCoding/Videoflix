from django.contrib import admin
from video_content_app.models import Video


class VideoAdmin(admin.ModelAdmin):
    """Admin configuration for the Video model.

    Provides a searchable, filterable list view for videos in the
    Django admin, and hides the raw video file field once a video
    already exists (editing the file directly in the admin would
    bypass the HLS conversion pipeline triggered via signals).
    """
    list_display = ('title', 'category', 'created_at')
    list_filter = ('category', 'created_at')
    search_fields = ('title', 'description')

    def get_exclude(self, request, obj=None):
        """Exclude the ``video_file`` field when editing an existing video.

        The field stays visible when *creating* a new video (obj is
        None) so uploads still work, but is hidden afterwards since
        replacing the file post-creation would not re-trigger the
        HLS conversion and could leave stale renditions on disk.

        Args:
            request: The current admin HttpRequest.
            obj: The Video instance being edited, or None when adding.

        Returns:
            tuple: Field names to exclude from the admin form.
        """
        exclude = super().get_exclude(request, obj) or ()
        if obj is not None:
            return exclude + ('video_file',)
        return exclude


admin.site.register(Video, VideoAdmin)
