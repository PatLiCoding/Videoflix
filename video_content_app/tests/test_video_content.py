import tempfile
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from auth_app.models import User
from video_content_app.models import Video
from video_content_app.services.utils import get_hls_output_dir


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class VideoTestsHappyPath(APITestCase):
    """Happy-path tests for the video API: authenticated access to
    the video list, the HLS master playlist, and an HLS segment,
    all against fake but present files on disk.
    """

    def setUp(self):
        """Create an authenticated user, a video, and fake HLS output files."""
        self.user = User.objects.create_user(
            username='testuser', email='test@example.com',
            password='securepassword123')
        self.video = Video.objects.create(
            title="Movie Title", description="Movie",
            category="Drama")
        self.client.force_authenticate(user=self.user)
        output_dir = get_hls_output_dir(self.video.id, '720p')
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / 'index.m3u8').write_text('#EXTM3U\n#EXT-X-ENDLIST\n')
        (output_dir / '001.ts').write_text('fake segment data')
        self.video_url = reverse('video')
        self.master_playlist_url = reverse('video-master-playlist', kwargs={
            'movie_id': self.video.id, 'resolution': '720p'})
        self.video_segment_url = reverse('video-segment', kwargs={
            'movie_id': self.video.id, 'resolution': '720p',
            'segment': '001.ts'})

    def test_get_list_video_return_200(self):
        """An authenticated request to the video list returns 200."""
        response = self.client.get(self.video_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_master_playlist_return_200(self):
        """An authenticated request for an existing playlist returns
        200 with the correct HLS content type."""
        response = self.client.get(self.master_playlist_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response['Content-Type'], 'application/vnd.apple.mpegurl')

    def test_get_video_segment_return_200(self):
        """
        An authenticated request for an existing .ts segment returns
        200 with the correct content type.
        """
        response = self.client.get(self.video_segment_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response['Content-Type'], 'video/MP2T')


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class VideoTestsUnhappyPath(APITestCase):
    """
    Unhappy-path tests for the video API: missing authentication,
    missing videos, missing files on disk, and invalid segment names.
    """

    def setUp(self):
        """
        Create a user and video, plus a playlist file but no
        video segment, to exercise the various 404/401 cases.
        """
        self.user = User.objects.create_user(
            username='testuser', email='test@example.com',
            password='securepassword123')
        self.video = Video.objects.create(
            title="Movie Title", description="Movie",
            category="Drama")
        output_dir = get_hls_output_dir(self.video.id, '720p')
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / 'index.m3u8').write_text('#EXTM3U\n#EXT-X-ENDLIST\n')
        self.video_url = reverse('video')
        self.master_playlist_url = reverse('video-master-playlist', kwargs={
            'movie_id': self.video.id, 'resolution': '720p'})

    def test_get_list_video_return_401(self):
        """An unauthenticated request to the video list returns 401."""
        response = self.client.get(self.video_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_master_playlist_return_404_when_file_missing(self):
        """Requesting a resolution with no generated playlist file
        returns 404."""
        self.client.force_authenticate(user=self.user)
        url = reverse('video-master-playlist', kwargs={
            'movie_id': self.video.id, 'resolution': '1080p'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_master_playlist_return_404_when_video_not_found(self):
        """Requesting a playlist for a nonexistent video id returns 404."""
        self.client.force_authenticate(user=self.user)
        url = reverse('video-master-playlist', kwargs={
            'movie_id': 999, 'resolution': '720p'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_video_segment_return_404_when_file_missing(self):
        """Requesting a segment file that was never generated returns 404."""
        self.client.force_authenticate(user=self.user)
        url = reverse('video-segment', kwargs={
            'movie_id': self.video.id, 'resolution': '720p',
            'segment': '001.ts'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_video_segment_return_404_when_video_not_found(self):
        """Requesting a segment for a nonexistent video id returns 404."""
        self.client.force_authenticate(user=self.user)
        url = reverse('video-segment', kwargs={
            'movie_id': 999, 'resolution': '720p',
            'segment': '001.ts'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_video_segment_return_404_when_segment_invalid(self):
        """
        A segment name that doesn't match the \\d{3}.ts pattern
        (e.g. path traversal or arbitrary filenames) returns 404.
        """
        self.client.force_authenticate(user=self.user)
        url = reverse('video-segment', kwargs={
            'movie_id': self.video.id, 'resolution': '720p',
            'segment': 'abc.ts'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_video_segment_return_401(self):
        """An unauthenticated request for a segment returns 401."""
        url = reverse('video-segment', kwargs={
            'movie_id': self.video.id, 'resolution': '720p',
            'segment': '001.ts'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
