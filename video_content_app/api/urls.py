from django.urls import path
from video_content_app.api.views import VideoView

urlpatterns = [
    path('video/', VideoView.as_view(), name='video'),
]
