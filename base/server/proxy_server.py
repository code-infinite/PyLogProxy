from http.server import HTTPServer
from typing import TYPE_CHECKING

from plugins.interceptor import (InterceptorPlugin,
                                 InvalidInterceptorPluginException,
                                 RequestInterceptorPlugin,
                                 ResponseInterceptorPlugin)

from ..handlers.ca import CertificateAuthority
from ..handlers.request_handler import ProxyRequestHandler

if TYPE_CHECKING:
    from typing import Any

__author__ = 'Rushirajsinh Chudasama'
__copyright__ = 'Copyright 2025, PyLogProxy Project'
__credits__ = ['Rushirajsinh Chudasama']

__license__ = 'MIT'
__status__ = 'Development'

__all__ = [
    'BaseProxyServer'
]


class BaseProxyServer(HTTPServer):
    def __init__(self, server_address: 'tuple[str,int]',
                 RequestHandlerClass: 'type[ProxyRequestHandler]',
                 bind_and_activate: 'bool'):
        HTTPServer.__init__(self, server_address,
                            RequestHandlerClass,  # type:ignore
                            bind_and_activate)
        self.ca = CertificateAuthority()
        self.res_plugins: 'list[type[ResponseInterceptorPlugin]]' = []
        self.req_plugins: 'list[type[RequestInterceptorPlugin]]' = []

    def register_interceptor(self, interceptor_class: 'Any'):
        if not issubclass(interceptor_class, InterceptorPlugin):
            raise InvalidInterceptorPluginException(
                f'Expected type InterceptorPlugin got {type(interceptor_class)} instead')
        if issubclass(interceptor_class, RequestInterceptorPlugin):
            self.req_plugins.append(interceptor_class)
        if issubclass(interceptor_class, ResponseInterceptorPlugin):
            self.res_plugins.append(interceptor_class)
