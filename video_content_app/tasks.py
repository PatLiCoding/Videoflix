import subprocess
from pathlib import Path
from django.conf import settings

RESOLUTIONS = {
    '480p': '854:480',
    '720p': '1280:720',
    '1080p': '1920:1080',
}


def get_hls_output_dir(movie_id, resolution):
    return Path(settings.MEDIA_ROOT) / 'videos' / 'hls' / str(movie_id) / resolution


def build_hls_command(source, output_dir, scale):
    playlist_path = output_dir / 'index.m3u8'
    segment_path = output_dir / '%03d.ts'
    return [
        'ffmpeg', '-i', str(source),
        '-vf', f'scale={scale}',
        '-c:v', 'libx264', '-crf', '23', '-c:a', 'aac',
        '-hls_time', '6', '-hls_list_size', '0',
        '-hls_segment_filename', str(segment_path),
        str(playlist_path),
    ]


def convert_to_hls(source, movie_id, resolution):
    scale = RESOLUTIONS[resolution]
    output_dir = get_hls_output_dir(movie_id, resolution)
    output_dir.mkdir(parents=True, exist_ok=True)
    cmd = build_hls_command(source, output_dir, scale)
    subprocess.run(cmd, capture_output=True, check=True)


def convert_all_resolutions(video_id):
    from .models import Video
    video = Video.objects.get(id=video_id)
    source = video.video_file.path
    for resolution in RESOLUTIONS:
        convert_to_hls(source, video_id, resolution)
