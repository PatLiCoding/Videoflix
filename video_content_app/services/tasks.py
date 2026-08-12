import subprocess
from video_content_app.services.utils import get_hls_output_dir, \
    build_hls_command
from video_content_app.models import Video

RESOLUTIONS = {
    '480p': '854:480',
    '720p': '1280:720',
    '1080p': '1920:1080',
}


def convert_to_hls(source, movie_id, resolution):
    scale = RESOLUTIONS[resolution]
    output_dir = get_hls_output_dir(movie_id, resolution)
    output_dir.mkdir(parents=True, exist_ok=True)
    cmd = build_hls_command(source, output_dir, scale)
    subprocess.run(cmd, capture_output=True, check=True)


def convert_all_resolutions(video_id):
    video = Video.objects.get(id=video_id)
    source = video.video_file.path
    for resolution in RESOLUTIONS:
        convert_to_hls(source, video_id, resolution)
