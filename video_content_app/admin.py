from django.contrib import admin
from video_content_app.models import Video


class VideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'created_at')
    list_filter = ('category', 'created_at')
    search_fields = ('title', 'description')

    def get_exclude(self, request, obj=None):
        exclude = super().get_exclude(request, obj) or ()
        if obj is not None:
            return exclude + ('video_file',)
        return exclude


admin.site.register(Video, VideoAdmin)
