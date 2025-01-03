""" Proxy handler that uses plugin for processing data"""

from typing import TYPE_CHECKING

from base.handlers.request_handler import ProxyRequestHandler

if TYPE_CHECKING:
    from plugins.interceptor import (RequestInterceptorPlugin,
                                     ResponseInterceptorPlugin)

__author__ = 'Rushirajsinh Chudasama'
__copyright__ = 'Copyright 2025, PyLogProxy Project'
__credits__ = ['Rushirajsinh Chudasama']

__license__ = 'MIT'
__status__ = 'Development'

__all__ = [
    "PluginProxyHandler"
]


class PluginProxyHandler(ProxyRequestHandler):

    def build_request(self) -> 'bytes':
        self.logger.info("*** REQUEST ***")
        plugin: 'type[RequestInterceptorPlugin]'
        for plugin in self.server.req_plugins:
            plugin(server=self.server,
                   http_message_handler=self).process_request()
        data: 'bytes' = super().build_request()
        self.logger.info("*** END REQUEST ***\n\n")
        return data

    def build_response(self) -> 'bytes':
        self.logger.info("*** RESPONSE ***")
        plugin: 'type[ResponseInterceptorPlugin]'
        for plugin in self.server.res_plugins:
            plugin(server=self.server,
                   http_message_handler=self).process_response()
        data: 'bytes' = super().build_response()
        self.logger.info("*** END RESPONSE ***")
        return data
