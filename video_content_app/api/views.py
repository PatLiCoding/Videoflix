from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from auth_app.api.authentications import JWTCookieAuthentication
from video_content_app.models import Video
from video_content_app.api.serializers import VideoSerializer


class VideoView(generics.ListAPIView):
    authentication_classes = [JWTCookieAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
