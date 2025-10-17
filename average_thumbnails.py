import argparse
import re
import sys
import textwrap
import time
from gettext import gettext as _
from io import BytesIO
from pathlib import Path

import numpy as np
import requests
from PIL import Image
from yt_dlp import YoutubeDL

from image_util import average_blend, median_blend, geometric_mean_blend, overlay_blend, max_blend, min_blend, crop_black_bars, resize_images

# huge thank you to eden for the insane amount of help, and thank you to all other contributers for bringing your ideas to the table.

# wait time in between channels to avoid yt rate limit (kinda redundant so u can keep it at 0)
SLEEP_TIME = 0

ANIMATION_FRAME_DURATION = 0.2

CHANNEL_REGEX = re.compile(r'^(?:https?://)?(?:www\.|m\.)?youtube\.com(?:/c)?/([^/]+)(?:/videos)?$')


def download_playlist_video_ids(playlist_url: str, max_videos: int, yt_dlp_opts: dict):
    yt_dlp_opts = yt_dlp_opts | {
        'extract_flat': True,
        # format for playlist_items is `[start]:[stop][:stride]`, where `[:stride]` is optional and if included also needs a colon in front of it
        'playlist_items': f'0:{max_videos * 2}',  # overshoot so that hopefully we get enough videos we don't filter out
    }

    with YoutubeDL(yt_dlp_opts) as ydl:
        try:
            info = ydl.extract_info(playlist_url, download=False)
            entries = info.get('entries', [])
            return [e['id'] for e in entries if 'id' in e][:max_videos * 2]
        except Exception as e:
            print(f'(╥‸╥) video list extraction failed.')
            print(e)
            return []


def download_video_thumbnails(video_ids: list[str], max_videos: int, thumbnail_folder: Path, yt_dlp_opts: dict) -> list[Image.Image]:
    thumbnails: list[Image.Image] = []

    with YoutubeDL(yt_dlp_opts) as ydl:
        for video_id in video_ids:
            if len(thumbnails) >= max_videos:
                break

            try:
                thumbnail_path = thumbnail_folder / f'{video_id}.png'

                if thumbnail_path.exists():
                    try:
                        thumbnail_image = Image.open(thumbnail_path)
                        thumbnails.append(thumbnail_image)
                        print(f"  ✔  [{len(thumbnails)}/{max_videos}] {video_id} (already downloaded)")
                        continue
                    except Exception as e:
                        print(f'(╥‸╥) failed to open image from file {thumbnail_path}, falling back to download: {e}')

                video = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)

                width = video.get("width")
                height = video.get("height")
                aspect_ratio = width / height if width and height else None

                def print_skip_reason(reason: str):
                    print(f"  ✘  skipped {reason} {video['title']}")

                if aspect_ratio is not None and aspect_ratio < 1:
                    print_skip_reason("for being a short!! (ew)")
                    continue
                elif video.get("is_live", False) or video.get("was_live", False):
                    print_skip_reason("for being a livestream!!")
                    continue

                thumbs = video.get('thumbnails')
                thumbs.sort(key=lambda thumb: thumb.get('preference', -9999), reverse=True)

                thumbnail_image = try_download_thumbnails(thumbs, video_id)

                if thumbnail_image is None:
                    print(f"(╥‸╥) skipping video, could not download thumbnail </3 id:{video_id}")
                    continue

                thumbnails.append(thumbnail_image)
                thumbnail_image.save(thumbnail_path)

                print(f"  ✔  [{len(thumbnails)}/{max_videos}] {video['title']}")
            except Exception as e:
                print(f"(╥‸╥) skipping video and pausing for 500 seconds </3 id:{video_id}")
                print(e)
                # time.sleep(500)

    print(" ")

    return thumbnails


url_templates = [
    'https://img.youtube.com/vi_webp/%s/maxresdefault.webp',
    'https://img.youtube.com/vi/%s/maxresdefault.jpg',
    'https://img.youtube.com/vi/%s/hqdefault.jpg',
]


def try_download_thumbnails(thumbnails: list[dict[str, object]], video_id: str) -> Image.Image | None:
    for thumbnail in thumbnails[:8]:  # only try first 8 thumbnails
        # noinspection PyTypeChecker
        thumbnail_url: str | None = thumbnail.get('url', None)

        if thumbnail_url is None:
            continue

        img = try_download_thumbnail(thumbnail_url)

        if img is not None:
            return img

    print(f"(╥‸╥) failed to download thumbnail for video {video_id}")
    return None


def try_download_thumbnail(url: str) -> Image.Image | None:
    response = requests.get(url)
    if response.status_code == 200:
        img = Image.open(BytesIO(response.content)).convert('RGB')

        w, h = img.size
        if w / h < 1.6:
            img = crop_black_bars(img)

        return img

    return None


def zleep_animation(total_seconds: int):
    zframes = ["𝗓   ", "  z  ", "    z", "     ", "     "]
    frame_idx = 0
    start = time.time()

    zbase_text = "avoiding rate limit..."
    while True:
        elapsed = time.time() - start
        if elapsed >= total_seconds:
            break
        sys.stdout.write(f"\r{zbase_text} {zframes[frame_idx]}    ")
        sys.stdout.flush()
        frame_idx = (frame_idx + 1) % len(zframes)
        time.sleep(ANIMATION_FRAME_DURATION)

    sys.stdout.write('\r' + ' ' * 69 + '\r')
    sys.stdout.flush()
    print()


HEADER_ANIMATION_FRAMES = ["OᴗO", "OᴗO", "OᴗO", ">ᴗ<", "OᴗO", ">ᴗ<", "OᴗO", "OᴗO", "OᴗO", ">ᴗ<"]


def print_starting_message():
    print()

    frame_idx = 0
    start = time.time()
    while True:
        elapsed = time.time() - start
        if elapsed > 3:
            break
        sys.stdout.write(f"\r  ✦︎  starting script {HEADER_ANIMATION_FRAMES[frame_idx]}  ✦︎")
        sys.stdout.flush()
        frame_idx = (frame_idx + 1) % len(HEADER_ANIMATION_FRAMES)
        time.sleep(ANIMATION_FRAME_DURATION)

    print("\n")
    print("˗ˏˋ SUBSCRIBE TO EMNERSON ˎˊ˗")
    print("\n")


class CustomHelpFormatter(argparse.MetavarTypeHelpFormatter):
    def _split_lines(self, text: str, width: int):
        """
        modified from argparse.RawTextHelpFormatter, but also dedents the string
        """
        splitlines = [textwrap.wrap(line, width) for line in text.splitlines()]
        return np.concatenate(splitlines).tolist()  # flatten list

    def _get_help_string(self, action: argparse.Action):
        """
        modified from argparse.ArgumentDefaultsHelpFormatter, but puts the default on a new line
        """
        # help = inspect.cleandoc(action.help.strip())
        help = textwrap.dedent(action.help).strip()
        print(f'cleaned:\n{help}')
        if help is None:
            help = ''

        if '%(default)' not in help:
            if action.default is not argparse.SUPPRESS:
                defaulting_nargs = [argparse.OPTIONAL, argparse.ZERO_OR_MORE]
                if action.option_strings or action.nargs in defaulting_nargs:
                    help = help + _('\n(default: %(default)s)')
        return help


def main():
    parser = argparse.ArgumentParser(
        description="""
        YouTube Thumbnail Averager
        
        by emnerson
        """,
        epilog='Subscribe to emnerson on youtube: https://www.youtube.com/emnersonn',
        formatter_class=CustomHelpFormatter
    )

    parser.add_argument(
        '--channels', '-c',
        help="""
        The playlists/youtube channels to process (separated by spaces)
        Can be in any of the following formats:
        - @channelname
        - channelname (WARNING: there are issues with it, it is much easier to just include the @)
        - https://www.youtube.com/@channelname
        """,
        required=True,
        type=str,
        nargs='+',
        default=[],
    )

    parser.add_argument(
        '--playlists', '-p',
        help='The playlists/youtube channels to process (separated by spaces)',
        type=str,
        nargs='+',
        default=[],
    )

    parser.add_argument(
        '--cookies',
        help='The path to the cookie file. This bypasses youtube age restrictions.\n'
             'See here how to make a cookie file: https://github.com/yt-dlp/yt-dlp/wiki/Extractors#exporting-youtube-cookies',
        type=str,
    )

    parser.add_argument(
        '--max-videos', '-m',
        help='The maximum number of videos to process',
        type=int,
        default=3000,
    )

    parser.add_argument(
        '--thumbnail-resolution', '-r',
        help='The thumbnail resolution to target, in [width]:[height]',
        type=str,
        default='1280:720',
    )

    parser.add_argument(
        '--average-blend',
        help='If an average blend of all the thumbnails should be created',
        type=bool,
        default=True,
        action=argparse.BooleanOptionalAction,
        choices=[True, False],
    )

    parser.add_argument(
        '--median-blend',
        help='If a median blend of all the thumbnails should be created',
        type=bool,
        default=True,
        action=argparse.BooleanOptionalAction,
        choices=[True, False],
    )

    parser.add_argument(
        '--geometric-mean-blend',
        help='If a geometric mean blend of all the thumbnails should be created',
        type=bool,
        default=True,
        action=argparse.BooleanOptionalAction,
        choices=[True, False],
    )

    parser.add_argument(
        '--overlay-blend',
        help='If an overlay blend of all the thumbnails should be created',
        type=bool,
        default=True,
        action=argparse.BooleanOptionalAction,
        choices=[True, False],
    )

    parser.add_argument(
        '--max-blend',
        help='If a max blend of all the thumbnails should be created',
        type=bool,
        default=True,
        action=argparse.BooleanOptionalAction,
        choices=[True, False],
    )

    parser.add_argument(
        '--min-blend',
        help='If a min blend of all the thumbnails should be created',
        type=bool,
        default=True,
        action=argparse.BooleanOptionalAction,
        choices=[True, False],
    )

    parser.add_argument(
        '--delete-thumbnails',
        help='If the individual thumbnails should be deleted after the blends are done',
        type=bool,
        default=False,
        action=argparse.BooleanOptionalAction,
        choices=[True, False],
    )

    args = parser.parse_args()

    urls: list[tuple[str, str]] = []

    for channel in args.channels:
        match = CHANNEL_REGEX.match(channel)
        if match:
            channel = match.group(1)

        urls.append((channel, f'https://www.youtube.com/{channel}/videos'))

    for playlist in args.playlists:
        urls.append((playlist, f'https://www.youtube.com/playlist?list={playlist}'))

    if not urls:
        parser.error('at least one of the following arguments are required: --channels/-c or --playlists/-p')

    max_videos = args.max_videos

    if max_videos <= 0:
        parser.error('max videos must be positive')

    yt_dlp_opts = {
        'quiet': True,
    }

    if args.cookies:
        yt_dlp_opts['cookiefile'] = args.cookies

    thumbnail_resolution = args.thumbnail_resolution.split(':')
    if len(thumbnail_resolution) != 2:
        parser.error('thumbnail resolution must be in format [width]:[height], for example 1280:720')

    try:
        thumbnail_resolution = [int(value) for value in thumbnail_resolution]
    except ValueError:
        parser.error('thumbnail resolution must be in format [width]:[height], for example 1280:720')

    print_starting_message()

    for idx, (playlist_id, playlist_url) in enumerate(urls):
        print(" ")
        print(f">> SOURCE {idx + 1}/{len(urls)}: {playlist_id}")

        playlist_folder = Path(f'playlists/{playlist_id}')
        thumbnail_folder = playlist_folder / 'thumbnails'
        thumbnail_folder.mkdir(parents=True, exist_ok=True)

        video_ids = download_playlist_video_ids(playlist_url, max_videos, yt_dlp_opts)

        video_thumbnails = download_video_thumbnails(video_ids, max_videos, thumbnail_folder, yt_dlp_opts)

        if not video_thumbnails:
            print(f"(╥‸╥) skipping {playlist_id}, evil scary error happened.")
            continue
            
        video_thumbnails = resize_images(video_thumbnails, thumbnail_resolution)

        if video_thumbnails:
            print(" ")
            generate_blended_thumbnails(args, playlist_folder, video_thumbnails)
            if args.delete_thumbnails:
                print("  ✩ deleting individual thumbnails...")
                for thumb in thumbnail_folder.iterdir():
                    thumb.unlink()
                thumbnail_folder.rmdir()
            print(" ")
            print(f"♡ {idx + 1} done!")
            print(" ")
        else:
            print(f"(╥‸╥) no thumbnails downloaded for {playlist_id}... smth went wrong D:")

        if idx <= len(urls):
            zleep_animation(SLEEP_TIME)

        print("one moment please...")
        print(""" 
    ／!、
  （ﾟ､｡ ７
    !  ~ヽ
    じし_,)ノ
boneless chicken""")
        print(" ")


def generate_blended_thumbnails(args, playlist_folder: Path, thumbnails: list[Image.Image]):
    if args.average_blend:
        print("  ✩ creating average blend...")
        average_blend(thumbnails).save(playlist_folder / 'average_thumbnail.png')

    if args.median_blend:
        print("  ✩ creating median blend...")
        median_blend(thumbnails).save(playlist_folder / 'median_thumbnail.png')

    if args.geometric_mean_blend:
        print("  ✩ creating geometric mean blend...")
        geometric_mean_blend(thumbnails).save(playlist_folder / 'geometric_mean_thumbnail.png')

    if args.overlay_blend:
        print("  ✩ creating overlay blend...")
        overlay_blend(thumbnails).save(playlist_folder / 'overlay_blend_thumbnail.png')

    if args.max_blend:
        print("  ✩ creating max blend...")
        max_blend(thumbnails).save(playlist_folder / 'max_thumbnail.png')

    if args.min_blend:
        print("  ✩ creating min blend...")
        min_blend(thumbnails).save(playlist_folder / 'min_thumbnail.png')


if __name__ == "__main__":
    main()
