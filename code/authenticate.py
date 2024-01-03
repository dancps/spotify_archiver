from spotipy.oauth2 import SpotifyOAuth  # ,SpotifyClientCredentials


class Authentication:
    def __init__(self, scope="playlist-read-private", method='oauth') -> None:
        self.scope = scope
        if method == 'oauth':
            self.auth = SpotifyOAuth(scope=scope)
        else:
            raise NotImplementedError(f"Authentication with {method} type doesn't exist or it hasn't been developed yet.")
    
    def get_auth(self):
        return self.auth