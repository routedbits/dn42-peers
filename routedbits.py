#
#
#

from requests import Session


class RoutedBitsNotFound(Exception):
    def __init__(self):
        super().__init__('Not Found')

class RoutedBitsTooManyArguments(Exception):
    def __init__(self):
        super().__init__('Too many arguments')


class RoutedBits(object):
    BASE = 'https://dn42.routedbits.com'

    def __init__(self):
        self._session = Session()

    def _request(self, method, path, params=None, data=None):
        url = f'{self.BASE}{path}'
        resp = self._session.request(method, url, params=params, json=data)
        if resp.status_code == 404:
            raise RoutedBitsNotFound()
        resp.raise_for_status()
        return resp

    def nodes(self, minimal=False, sort_by='city'):
        path = '/nodes.json'
        resp = self._request('GET', path).json()['regions']

        nodes = resp
        if minimal:
            nodes = []
            for region in resp:
                nodes.extend(region['sites'])
            nodes = sorted(nodes, key=lambda node: node[sort_by])

        return nodes

    def node(self, hostname=None, name=None):
        if hostname and name:
            raise RoutedBitsTooManyArguments()

        nodes = self.nodes(minimal=True)
        for node in nodes:
            if hostname:
                if node['hostname'] == hostname:
                    return node

            if name:
                if node['name'] == name:
                    return node

        raise RoutedBitsNotFound()
