from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from auth_app.models import User
from video_content_app.models import Video


class VideoTestsHappyPath(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', email='test@example.com',
            password='securepassword123')
        self.video = Video.objects.create(
            title="Movie Title", description="Movie",
            thumbnail_url="http://example.com/media/thumbnail/image.jpg",
            category="Drama")
        self.video2 = Video.objects.create(
            title="Movie Title", description="Movie",
            thumbnail_url="http://example.com/media/thumbnail/image.jpg",
            category="Drama")
        self.client.force_authenticate(user=self.user)
        self.video_url = reverse('video')

    def test_get_list_video_return_200(self):
        response = self.client.get(self.video_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class VideoTestsUnhappyPath(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', email='test@example.com',
            password='securepassword123')
        self.video = Video.objects.create(
            title="Movie Title", description="Movie",
            thumbnail_url="http://example.com/media/thumbnail/image.jpg",
            category="Drama")
        self.video2 = Video.objects.create(
            title="Movie Title", description="Movie",
            thumbnail_url="http://example.com/media/thumbnail/image.jpg",
            category="Drama")
        self.video_url = reverse('video')

    def test_get_list_video_return_401(self):
        response = self.client.get(self.video_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
