#
#
#

from requests import Session


class RegistryNotFound(Exception):
    def __init__(self):
        super().__init__('Object Not Found')


class Registry(object):
    BASE = 'https://explorer.dn42.dev/api/registry'

    def __init__(self):
        self._session = Session()

    def _request(self, method, path, params=None, data=None):
        url = f'{self.BASE}{path}'
        resp = self._session.request(method, url, params=params, json=data)
        if resp.status_code == 404:
            raise RegistryNotFound()
        resp.raise_for_status()
        return resp

    def asns(self):
        path = '/aut-num'
        return self._request('GET', path).json()['aut-num']

    def asn(self, asn):
        path = f'/aut-num/AS{asn}'
        return self._request('GET', path).json()
