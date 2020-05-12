# Spotify archiver

## Usage
To use this code you can import [`archive.py`](./code/archive.py) functions or, if you just want the default archive process, use this command:
```
python code/archive.py -u [user]
```

In order to make the program run, you'll need to get an authentication token and save it in `.auth/token.txt`. Note that this **is not** the safest approach to authenticating an application. Use at your own risk.

For more options use the command `python code/archive.py -h`.

## Requirements
This code was made in Python 3.6.9, so it may work well on any 3.x version.

To install Python dependencies, just use the pip command:
```
pip install -r requirements.txt
```

## How to get an authentication token
To get an authentication token in [Spotify's console](https://developer.spotify.com/console/get-playlists/) just click in the **Get Token** button and select `playlist-read-private` and `playlist-read-collaborative` flags, then copy the token into `.auth/token.txt`.

![authentication token](./docs/img/auth.png)

![Permission scope](./docs/img/scope.png)

**Warning:** This is not the safest way of authenticating an application. I'm still learning how to automate this in the safest way, but at this point the plain text method is the one used.

