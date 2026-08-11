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
