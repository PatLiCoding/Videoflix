import re
from django.http import FileResponse
from django.shortcuts import get_object_or_404

from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from auth_app.api.authentications import JWTCookieAuthentication
from video_content_app.models import Video
from video_content_app.tasks import get_hls_output_dir
from video_content_app.api.serializers import VideoSerializer


class VideoView(generics.ListAPIView):
    authentication_classes = [JWTCookieAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Video.objects.all()
    serializer_class = VideoSerializer


class HLSMasterPlaylistView(APIView):
    authentication_classes = [JWTCookieAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, movie_id, resolution):
        try:
            get_object_or_404(Video, id=movie_id)
            output_dir = get_hls_output_dir(movie_id, resolution)
            playlist_path = output_dir / 'index.m3u8'
            return FileResponse(
                open(playlist_path, 'rb'),
                content_type='application/vnd.apple.mpegurl')
        except FileNotFoundError:
            return Response(status=status.HTTP_404_NOT_FOUND)


class HLSVideoSegmentView(APIView):
    authentication_classes = [JWTCookieAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, movie_id, resolution, segment):
        if not re.fullmatch(r'\d{3}\.ts', segment):
            return Response(status=status.HTTP_404_NOT_FOUND)
        try:
            get_object_or_404(Video, id=movie_id)
            output_dir = get_hls_output_dir(movie_id, resolution)
            segment_path = output_dir / segment
            return FileResponse(
                open(segment_path, 'rb'),
                content_type='video/MP2T')
        except FileNotFoundError:
            return Response(status=status.HTTP_404_NOT_FOUND)
