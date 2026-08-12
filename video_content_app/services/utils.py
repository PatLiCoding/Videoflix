from pathlib import Path
from django.conf import settings


def get_hls_output_dir(movie_id, resolution):
    """Build the filesystem path where a video's HLS output is stored.

    Renditions are laid out as
    ``MEDIA_ROOT/videos/hls/<movie_id>/<resolution>/`` so that the
    playlist and segment API views can locate files for a given
    video/resolution pair, and so the app config's cleanup logic can
    remove a video's whole output tree by id.

    Args:
        movie_id (int): Primary key of the related Video instance.
        resolution (str): Resolution label, e.g. '720p'.

    Returns:
        pathlib.Path: Directory path for that video's HLS output at
        the given resolution (not guaranteed to exist yet).
    """
    base_dir = Path(settings.MEDIA_ROOT) / 'videos' / 'hls'
    return base_dir / str(movie_id) / resolution


def build_hls_command(source, output_dir, scale):
    """Assemble the ffmpeg command line for HLS transcoding.

    Produces a single-rendition HLS output: an ``index.m3u8``
    playlist referencing sequentially numbered ``%03d.ts`` segments,
    encoded with H.264/AAC at a fixed CRF and 6-second segment length.

    Args:
        source (str): Path to the source video file.
        output_dir (pathlib.Path): Directory to write the playlist
            and segments into.
        scale (str): ffmpeg scale filter value, e.g. '1280:720'.

    Returns:
        list[str]: The ffmpeg command as an argument list, suitable
        for ``subprocess.run``.
    """
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
