"""URL routes for the video content API.
Exposes three endpoints:
    - GET /video/                                  -> list all videos
    - GET /video/<movie_id>/<resolution>/index.m3u8 -> HLS master playlist
    - GET /video/<movie_id>/<resolution>/<segment>/ -> HLS video segment (.ts)
All three require JWT authentication (enforced in the views).
"""
from django.urls import path
from video_content_app.api.views import VideoView, \
    HLSMasterPlaylistView, HLSVideoSegmentView

urlpatterns = [
    path('video/', VideoView.as_view(), name='video'),
    path('video/<int:movie_id>/<str:resolution>/index.m3u8',
         HLSMasterPlaylistView.as_view(), name='video-master-playlist'),
    path('video/<int:movie_id>/<str:resolution>/<str:segment>/',
         HLSVideoSegmentView.as_view(), name='video-segment'),
]
