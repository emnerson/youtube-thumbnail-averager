**if you're using my code, all i ask is that u subscribe to my channel! :> [youtube.com/emnersonn](https://youtube.com/emnersonn)**

also hi code ppl if anything here is stupid or makes like no sense please yell at me on twitter, i have never put anything on github before so i follor a tutorial... don't yell at me for my bad code though i already know that it sucks.

this script downloads thumbnails from YT channels (or playlists if you want) and blends them into one image.

# installation

create a venv (`python3 -m venv .venv`), go into it and run `pip3 install -r requirements.txt`. 

# usage

once everything's set up, go to a youtube thumbnail grabber website (i use [YTLarge](https://ytlarge.com)) and get the id of the channel you wanna blend. the id is the part that starts with UC.

you can run the program by executing `python3 average_thumbnails.py [channel_id]:[max_thumbnails]`.

example for [emnerson](https://youtube.com/emnersonn) and 100 thumbnails: `python3 average_thumbnails.py UC11zGVkBKRBp5FX8uaWLqjw:100`

# other notes

requirements for those who don't feel like looking at the [req file](./requirements.txt):
- Python 3.x
- yt-dlp
- Pillow
- NumPy
- requests

remember, you can install this all automatically by running `pip3 install -r requirements.txt`.