"""Logging proxy handler to log requests and responses."""


from base import app
from base.server.async_proxy_server import AsyncBaseProxyServer
from base.server.proxy_server import BaseProxyServer
from plugins.interceptor import DebugInterceptor
from plugins.plugin_proxy_handler import PluginProxyHandler

__author__ = 'Rushirajsinh Chudasama'
__copyright__ = 'Copyright 2025, PyLogProxy Project'
__credits__ = ['Rushirajsinh Chudasama']

__license__ = 'MIT'
__status__ = 'Development'

__all__ = [
    'LoggingProxy',
    'AsyncLoggingProxy'
]


class LoggingProxy(BaseProxyServer):
    def __init__(self, server_address: 'tuple[str,int]' = (app['host'], app['port']),
                 RequestHandlerClass: 'type[PluginProxyHandler]' = PluginProxyHandler,
                 bind_and_activate: 'bool' = True) -> 'None':
        super().__init__(server_address, RequestHandlerClass,
                         bind_and_activate)
        self.register_interceptor(interceptor_class=DebugInterceptor)


class AsyncLoggingProxy(AsyncBaseProxyServer):
    def __init__(self, server_address: 'tuple[str,int]' = (app['host'], app['port']),
                 RequestHandlerClass: 'type[PluginProxyHandler]' = PluginProxyHandler,
                 bind_and_activate: 'bool' = True) -> 'None':
        super().__init__(server_address, RequestHandlerClass,
                         bind_and_activate)
        self.register_interceptor(interceptor_class=DebugInterceptor)
