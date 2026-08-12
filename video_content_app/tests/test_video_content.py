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

    def setUp(self):
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
        response = self.client.get(self.video_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_master_playlist_return_200(self):
        response = self.client.get(self.master_playlist_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response['Content-Type'], 'application/vnd.apple.mpegurl')

    def test_get_video_segment_return_200(self):
        response = self.client.get(self.video_segment_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response['Content-Type'], 'video/MP2T')


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class VideoTestsUnhappyPath(APITestCase):

    def setUp(self):
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
        response = self.client.get(self.video_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_master_playlist_return_404_when_file_missing(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('video-master-playlist', kwargs={
            'movie_id': self.video.id, 'resolution': '1080p'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_master_playlist_return_404_when_video_not_found(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('video-master-playlist', kwargs={
            'movie_id': 999, 'resolution': '720p'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_video_segment_return_404_when_file_missing(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('video-segment', kwargs={
            'movie_id': self.video.id, 'resolution': '720p',
            'segment': '001.ts'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_video_segment_return_404_when_video_not_found(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('video-segment', kwargs={
            'movie_id': 999, 'resolution': '720p',
            'segment': '001.ts'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_video_segment_return_404_when_segment_invalid(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('video-segment', kwargs={
            'movie_id': self.video.id, 'resolution': '720p',
            'segment': 'abc.ts'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_video_segment_return_401(self):
        url = reverse('video-segment', kwargs={
            'movie_id': self.video.id, 'resolution': '720p',
            'segment': '001.ts'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
