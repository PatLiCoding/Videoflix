from pathlib import Path
from django.conf import settings


def get_hls_output_dir(movie_id, resolution):
    base_dir = Path(settings.MEDIA_ROOT) / 'videos' / 'hls'
    return base_dir / str(movie_id) / resolution


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
