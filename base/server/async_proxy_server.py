from socketserver import ThreadingMixIn

from .proxy_server import BaseProxyServer

__author__ = 'Rushirajsinh Chudasama'
__copyright__ = 'Copyright 2025, PyLogProxy Project'
__credits__ = ['Rushirajsinh Chudasama']

__license__ = 'MIT'
__status__ = 'Development'

__all__ = [
    'AsyncBaseProxyServer'
]


class AsyncBaseProxyServer(ThreadingMixIn, BaseProxyServer):
    pass
