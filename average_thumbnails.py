#!/usr/bin/env python3

import argparse
import yt_dlp
from PIL import Image
import numpy as np
import requests
from io import BytesIO
import os
import time
import sys
import shutil

# channel ids go here with UU instead of UC and you can set the max videos you want it to download by putting a number after the comma.
#! DISREGARD! Use arguments to input the channels or use `--old` to use this!
IDS_AND_MAX_VIDEOS = [("UUKqH_9mk1waLgBiL2vT5b9g", 3000),("UU4rqhyiTs7XyuODcECvuiiQ", 3000)]

# wait time in between channels to avoid yt rate limit (kinda redundant so u can keep it at 0)
SLEEP_TIME = 0
"""
# sort by video length
LONGEST_SHORT = 180
SHORTEST_LIVE = 4800
"""
THUMBNAIL_SIZE = (1280, 720)

def zleep_animation(total_seconds):
    zframes = ["𝗓   ", "  z  ", "    z","     ","     "]
    frame_idx = 0
    start = time.time()

    zbase_text = "avoiding rate limit..."
    while True:
        elapsed = time.time() - start
        if elapsed >= total_seconds:
            break
        zframe = zframes[frame_idx]
        zmessage = f"\r{zbase_text} {zframe}    "
        sys.stdout.write(zmessage)
        sys.stdout.flush()
        frame_idx = (frame_idx + 1) % len(zframes)
        time.sleep(.4)

    sys.stdout.write('\r' + ' ' * 69 + '\r')
    sys.stdout.flush()
    print()

def start_animation():
    sframes = ["OᴗO","OᴗO","OᴗO",">ᴗ<","OᴗO",">ᴗ<","OᴗO","OᴗO","OᴗO",">ᴗ<",]
    frame_idx = 0
    start = time.time()

    sbase_text_one = "  ✦︎  starting script "
    sbase_text_two = "  ✦︎"
    while True:
        elapsed = time.time() - start
        if elapsed >= 3:
            break
        sframe = sframes[frame_idx]
        smessage = f"\r{sbase_text_one}{sframe}{sbase_text_two}    "
        sys.stdout.write(smessage)
        sys.stdout.flush()
        frame_idx = (frame_idx + 1) % len(sframes)
        time.sleep(.25)

def crop_black_bars(img, black_threshold=30, consecutive_rows=3):
    arr = np.array(img.convert('L'))
    h, w = arr.shape

    def is_black_row(row):
        return np.mean(row) < black_threshold

    top, bottom = 0, h
    for i in range(h):
        if all(is_black_row(arr[j]) for j in range(i, min(i + consecutive_rows, h))):
            top = i + consecutive_rows
        else:
            break
    for i in range(h - 1, -1, -1):
        if all(is_black_row(arr[j]) for j in range(max(0, i - consecutive_rows + 1), i + 1)):
            bottom = i - consecutive_rows + 1
        else:
            break

    left, right = 0, w
    for i in range(w):
        if all(is_black_row(arr[:, j]) for j in range(i, min(i + consecutive_rows, w))):
            left = i + consecutive_rows
        else:
            break
    for i in range(w - 1, -1, -1):
        if all(is_black_row(arr[:, j]) for j in range(max(0, i - consecutive_rows + 1), i + 1)):
            right = i - consecutive_rows + 1
        else:
            break

    if top >= bottom or left >= right:
        return img
    return img.crop((left, top, right, bottom))

def get_video_ids(playlist_url, max_videos):
    ydl_opts_flat = {'quiet': True, 'extract_flat': True, 'force_generic_extractor': True}

    print(" ")
    try:
        with yt_dlp.YoutubeDL(ydl_opts_flat) as ydl:
            info = ydl.extract_info(playlist_url, download=False)
            entries = info.get('entries', [])
            flat_ids = [e['id'] for e in entries if 'id' in e][:max_videos * 2]
    except Exception as e:
        print(f"(╥‸╥) video list extraction failed. {e}")
        return []

    ydl_opts_rich = {'quiet': True}
    filtered_ids, success_count = [], 0
    with yt_dlp.YoutubeDL(ydl_opts_rich) as ydl:
        for vid_id in flat_ids:
            try:
                video = ydl.extract_info(f"https://www.youtube.com/watch?v={vid_id}", download=False)

                width = video.get("width")
                height = video.get("height")
                aspect_ratio = round(width / height, 4) if width and height else None

                is_live = video.get("is_live", False)
                was_live = video.get("was_live", False)

                # duration = video.get("duration", 0)

                if aspect_ratio >= 1 and is_live == False and was_live == False:
                    filtered_ids.append(vid_id)
                    success_count += 1
                    print(f"  ✔  [{success_count}/{max_videos}] {video['title']}")
                else:
                    reason = "for being a short!! (ew)" if aspect_ratio <= 1 else \
                             "for being a current livestream!!" if is_live == True else \
                             "for being a past livestream!!" if was_live == True else \
                             "for.. uhh... i have no idea why actually"
                    
                    print(f"  ✘  skipped {reason} {video['title']}")
                """
                if LONGEST_SHORT <= duration <= SHORTEST_LIVE:
                    filtered_ids.append(vid_id)
                    success_count += 1
                    print(f"  ✔  [{duration}s] [{success_count}/{max_videos}] {video['title']}")
                else:
                    reason = "for being too short!!" if duration < LONGEST_SHORT else "for being too long!!"
                    print(f"  ✘  skipped {reason} [{duration}s] {video['title']}")
                """
                time.sleep(5)
                if len(filtered_ids) >= max_videos:
                    break
            except Exception:
                print(f"(╥‸╥) skipping video and pausing for 500 seconds </3 id:{vid_id}")
                time.sleep(500)
    print(" ")

    return filtered_ids

def download_thumbnail(video_id):
    urls = [
        f'https://img.youtube.com/vi/{video_id}/maxresdefault.jpg',
        f'https://img.youtube.com/vi/{video_id}/hqdefault.jpg',
    ]
    for url in urls:
        response = requests.get(url)
        if response.status_code == 200:
            try:
                img = Image.open(BytesIO(response.content)).convert('RGB')
                w, h = img.size
                if w / h < 1.6:
                    img = crop_black_bars(img)
                img = img.resize(THUMBNAIL_SIZE)
                time.sleep(0.5)
                return img
            except Exception as e:
                print(f"(╥‸╥) error resizing video {video_id}: {e}")
    print(f"(╥‸╥) failed to download thumbnail for video {video_id}")
    return None

def average_blend(thumbnails):
    stack = np.stack([np.array(img, dtype=np.float32) for img in thumbnails], axis=0)
    return Image.fromarray(np.mean(stack, axis=0).astype(np.uint8))

def median_blend(thumbnails):
    stack = np.stack([np.array(img, dtype=np.uint8) for img in thumbnails], axis=0)
    return Image.fromarray(np.median(stack, axis=0).astype(np.uint8))

def geometric_mean_blend(thumbnails):
    stack = np.stack([np.array(img, dtype=np.float32) + 1 for img in thumbnails], axis=0)
    geo_mean = np.exp(np.mean(np.log(stack), axis=0)) - 1
    return Image.fromarray(np.clip(geo_mean, 0, 255).astype(np.uint8))

def overlay_blend(thumbnails):
    stack = np.stack([np.array(img, dtype=np.float32) / 255 for img in thumbnails], axis=0)
    avg, multiplied = np.mean(stack, axis=0), np.prod(stack, axis=0)
    mask = avg <= 0.5
    overlay = np.zeros_like(avg)
    overlay[mask] = 2 * multiplied[mask] * avg[mask]
    overlay[~mask] = 1 - 2 * (1 - multiplied[~mask]) * (1 - avg[~mask])
    return Image.fromarray((overlay * 255).clip(0, 255).astype(np.uint8))

def max_blend(thumbnails):
    stack = np.stack([np.array(img, dtype=np.uint8) for img in thumbnails], axis=0)
    return Image.fromarray(np.max(stack, axis=0))

def min_blend(thumbnails):
    stack = np.stack([np.array(img, dtype=np.uint8) for img in thumbnails], axis=0)
    return Image.fromarray(np.min(stack, axis=0))

def main():
    print(" ")
    print(" ")
    print(" ")
    start_animation()
    print(" ")
    print("˗ˏˋ SUBSCRIBE TO EMNERSON ˎˊ˗") #! what about me >:(
    print("\n\n")
    time.sleep(1)

    playlists_root = "playlists"
    if os.path.exists(playlists_root):
        shutil.rmtree(playlists_root)

    for idx, (playlist_id, max_videos) in enumerate(IDS_AND_MAX_VIDEOS, start=1):
        playlist_url = f"https://www.youtube.com/playlist?list={playlist_id}"

        time.sleep(1)
        print(" ")
        print(f">> PLAYLIST {idx}/{len(IDS_AND_MAX_VIDEOS)}")

        video_ids = get_video_ids(playlist_url, max_videos)
        if not video_ids:
            print(f"(╥‸╥) skipping {playlist_id}, evil scary error happened.")
            continue

        playlist_folder = os.path.join("playlists", f"playlist_{idx}")
        thumbnail_folder = os.path.join(playlist_folder, "thumbnails")
        os.makedirs(thumbnail_folder, exist_ok=True)
        thumbnails = []

        for i, vid_id in enumerate(video_ids):
            print(f"  ↴ downloading thumbnail... {i+1}/{len(video_ids)}")
            thumb = download_thumbnail(vid_id)
            if thumb:
                thumbnails.append(thumb)
                thumb.save(f"{thumbnail_folder}/thumb_{i+1}.jpg")
            else:
                print(f"(╥‸╥) skipping video </3 id:{vid_id}")

        if thumbnails:
            time.sleep(1)
            print(" ")

            print("  ✩ creating average blend...")
            average_blend(thumbnails).save(f"{playlist_folder}/average_thumbnail.png")

            print("  ✩ creating median blend...")
            median_blend(thumbnails).save(f"{playlist_folder}/median_thumbnail.png")

            print("  ✩ creating geometric mean blend...")
            geometric_mean_blend(thumbnails).save(f"{playlist_folder}/geometric_mean_thumbnail.png")

            print("  ✩ creating overlay blend...")
            overlay_blend(thumbnails).save(f"{playlist_folder}/overlay_blend_thumbnail.png")

            print("  ✩ creating max blend...")
            max_blend(thumbnails).save(f"{playlist_folder}/max_thumbnail.png")

            print("  ✩ creating min blend...")
            min_blend(thumbnails).save(f"{playlist_folder}/min_thumbnail.png")

            print(" ")
            print(f"♡ {idx} done!")
            print(" ")
        else:
            print(f"(╥‸╥) no thumbnails downloaded for {playlist_id}... smth went wrong D:")

        time.sleep(1)

        if idx < len(IDS_AND_MAX_VIDEOS):
            zleep_animation(SLEEP_TIME)

        print(" ")
        print("one moment please...")
        time.sleep(2)
        print(""" 
    ／!、
  （ﾟ､｡ ７
    !  ~ヽ
    じし_,)ノ
boneless chicken""")
        print(" ")
        print(" ")

if __name__ == "__main__":
    parser = argparse.ArgumentParser("./average_thumbnails.py")
    parser.epilog = "yt average thumbnail averager by emnerson & contributors <3"
    parser.add_argument("ids", nargs="*", help="The YouTube channel ID and max video number, with both arguments separated by a colon")
    parser.add_argument("--old", help="Use the old way of inputting files (via the script file)", action="store_true")

    if len(sys.argv) == 1:
        parser.print_help()
        exit()

    args = parser.parse_args()

    if not args.old:
        if len(args.ids) == 0:
            print("You forgot the IDs (somehow)! >:(")
        
        IDS_AND_MAX_VIDEOS = [["UU" + id[2:], int(max)] for id, max in map(lambda s: s.split(":"), args.ids)] #* hehe i even replace the UC with UU automagically :3c

    main()