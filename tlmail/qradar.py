import requests
from requests.compat import urljoin


class QRadarAPI:
    def __init__(self, server: str, token: str, version: str = None) -> None:
        self.server = server
        self.token = token
        self.version = version

    def get_offenses(self, filter: str = None):
        url = urljoin(self.server, 'siem/offenses')

        params = {}
        if filter:
            params['filter'] = filter

        r = requests.get(
            url,
            headers={
                'Accept': 'application/json',
                'SEC': self.token,
                'Version': self.version,
            },
            params=params
        )
        return r.json()

    def get_offense(self, id: int):
        url = urljoin(self.server, f'siem/offenses/{id}')

        r = requests.get(
            url,
            headers={
                'Accept': 'application/json',
                'SEC': self.token,
                'Version': self.version,
            }
        )
        return r.json()
