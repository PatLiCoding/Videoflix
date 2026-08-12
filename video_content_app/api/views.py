import re
from django.http import FileResponse
from django.shortcuts import get_object_or_404

from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from auth_app.api.authentications import JWTCookieAuthentication
from video_content_app.models import Video
from video_content_app.services.utils import get_hls_output_dir
from video_content_app.api.serializers import VideoSerializer


class VideoView(generics.ListAPIView):
    """Lists all available videos.

    GET /api/video/

    Requires a valid JWT access token, read from an HttpOnly cookie
    via JWTCookieAuthentication (the project's global DRF auth setting
    only reads the Authorization header, so this is set explicitly
    here). Returns each video's metadata via VideoSerializer.
    """
    authentication_classes = [JWTCookieAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Video.objects.all()
    serializer_class = VideoSerializer


class HLSMasterPlaylistView(APIView):
    """Serves the HLS master playlist (index.m3u8) for one video/resolution.

    GET /api/video/<movie_id>/<resolution>/index.m3u8

    Requires JWT authentication. Returns 404 if the video does not
    exist or if the playlist file has not been generated yet (e.g.
    conversion still pending or failed).
    """
    authentication_classes = [JWTCookieAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, movie_id, resolution):
        """Return the .m3u8 playlist file as a streamed response.

        Args:
            request: The incoming DRF request.
            movie_id (int): Primary key of the Video.
            resolution (str): Requested resolution, e.g. '720p'.

        Returns:
            FileResponse: The playlist file with the correct
            Apple HLS MIME type, or a 404 Response if the video or
            playlist file is missing.
        """
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
    """Serves a single HLS video segment (.ts file).

    GET /api/video/<movie_id>/<resolution>/<segment>/

    Requires JWT authentication. The segment name is validated with a
    strict regex (three digits + ".ts") to reject malformed input and
    prevent path traversal before it is used to build a filesystem
    path. Returns 404 if the segment name is invalid, or if the
    video/segment file does not exist.
    """
    authentication_classes = [JWTCookieAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, movie_id, resolution, segment):
        """Return the requested .ts segment file as a streamed response.

        Args:
            request: The incoming DRF request.
            movie_id (int): Primary key of the Video.
            resolution (str): Requested resolution, e.g. '720p'.
            segment (str): Segment filename, expected format '\\d{3}.ts'.

        Returns:
            FileResponse: The video segment with MIME type
            'video/MP2T', or a 404 Response if the segment name is
            invalid or the file/video is missing.
        """
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
