import os
from danfault.logs import Loggir


class Authenticator:
    def __init__(self):
        self.client_id = os.environ.get("SPOTIFY_CLIENT_ID")
        self.client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")
        self.logger = Loggir()
        self.logger.info(f"Client ID: {self.client_id}")
        self.logger.info(f"Client Secret: {len(self.client_secret)*'*'}")


def main():
    auth = Authenticator()


if __name__ == "__main__":
    main()