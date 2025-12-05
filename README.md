**if you're using my code, all i ask is that u subscribe to my channel! :> [youtube.com/emnersonn](https://youtube.com/emnersonn)**

this script downloads thumbnails from YT channels (or playlists if you want) and blends them into one image.

# installation

create a venv (`python3 -m venv .venv`), go into it and run `pip3 install -r requirements.txt`. 

# usage

you can run the program by executing `python average_thumbnails.py --max-videos [# of videos you want downloaded] --channel "@[handle]"`.
for more information, execute `python average_thumbnails.py --help`

example for [emnerson](https://youtube.com/emnersonn) and 100 thumbnails: `python average_thumbnails.py --max-videos 100 --channel "@emnersonn"`

# other notes

requirements for those who don't feel like looking at the [req file](./requirements.txt):
- Python 3.x
- yt-dlp
- Pillow
- NumPy
- requests

remember, you can install this all automatically by running `pip3 install -r requirements.txt`.

If you encounter issues possibly try with the -mp flag to disable multiprocessing (It shouldn't make a diffrence but your mileage may vary)