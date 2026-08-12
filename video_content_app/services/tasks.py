import subprocess
from video_content_app.services.utils import get_hls_output_dir, \
    build_hls_command
from video_content_app.models import Video

# Maps a resolution label to the ffmpeg scale filter value
# ("width:height") used when transcoding.
RESOLUTIONS = {
    '480p': '854:480',
    '720p': '1280:720',
    '1080p': '1920:1080',
}


def convert_to_hls(source, movie_id, resolution):
    """Transcode a source video into HLS format for one resolution.

    Creates the target output directory if needed and runs ffmpeg
    synchronously to produce an ``index.m3u8`` playlist plus numbered
    ``.ts`` segments for the given resolution.

    Args:
        source (str): Filesystem path to the original video file.
        movie_id (int): Primary key of the related Video instance.
        resolution (str): One of the keys in RESOLUTIONS, e.g. '720p'.

    Raises:
        subprocess.CalledProcessError: If the ffmpeg command fails.
    """
    scale = RESOLUTIONS[resolution]
    output_dir = get_hls_output_dir(movie_id, resolution)
    output_dir.mkdir(parents=True, exist_ok=True)
    cmd = build_hls_command(source, output_dir, scale)
    subprocess.run(cmd, capture_output=True, check=True)


def convert_all_resolutions(video_id):
    """Convert a video into all supported HLS resolutions.

    This is the entry point enqueued by the post_save signal on
    Video (via django-rq) so that transcoding happens asynchronously
    in a worker process rather than blocking the upload request.

    Args:
        video_id (int): Primary key of the Video to convert.
    """
    video = Video.objects.get(id=video_id)
    source = video.video_file.path
    for resolution in RESOLUTIONS:
        convert_to_hls(source, video_id, resolution)
