""" Base module for proxy handler """

from http.client import HTTPResponse
from http.server import BaseHTTPRequestHandler
from logging import FileHandler, getLogger
from os import makedirs
from socket import create_connection
from ssl import CERT_OPTIONAL, Purpose, create_default_context
from typing import TYPE_CHECKING
from urllib.parse import ParseResult, urlparse, urlunparse
from uuid import uuid4

import certifi

from base import logger, request_log

if TYPE_CHECKING:
    from logging import Logger
    from socket import socket
    from typing import Any

    from server.proxy_server import BaseProxyServer

__author__ = 'Rushirajsinh Chudasama'
__copyright__ = 'Copyright 2025, PyLogProxy Project'
__credits__ = ['Rushirajsinh Chudasama']

__license__ = 'MIT'
__status__ = 'Development'

__all__ = [
    'ProxyRequestHandler'
]


class UnsupportedSchemeException(Exception):
    """ Exception for un supported http scheme. """
    pass


class ProxyRequestHandler(BaseHTTPRequestHandler):
    """ Base class for handling proxy connection """

    ca_file = certifi.where()

    def __init__(self, request: 'socket | tuple[bytes, socket]',
                 client_address: 'tuple[str, int] | str',
                 server: 'BaseProxyServer') -> 'None':

        self.is_connect = False
        self.hostname = ""
        self.port = 8000
        self.path = ""
        self.ssl_host = ""
        self._headers_buffer = []
        self.san: 'list[tuple[str,str]]' = []
        self.request_id = uuid4()
        self.logger: 'Logger' = getLogger(str(self.request_id))

        makedirs(name=request_log['dir'], exist_ok=True)

        self.logger.handlers.clear()
        self.logger.setLevel(request_log['level'].upper())

        # Create a file handler to log messages to a file
        file_handler = FileHandler(f'{request_log['dir']}/{self.request_id}.log')

        # Add handlers to the logger
        self.logger.addHandler(file_handler)

        BaseHTTPRequestHandler.__init__(self, request, client_address, server)

        self.server: 'BaseProxyServer'  # type:ignore
        self._proxy_sock: 'socket'

    def _connect_to_host(self) -> 'None':
        # Get hostname and port to connect to
        if self.is_connect:
            self.hostname, self.port = self.path.split(sep=':')
        else:
            u: 'ParseResult' = urlparse(url=self.path)
            if u.scheme != 'http':
                raise UnsupportedSchemeException(
                    f'Unknown scheme {repr(u.scheme)}')
            self.hostname = u.hostname or self.path.split(':')[0]
            self.port = u.port or 80
            self.path = urlunparse(
                components=ParseResult(
                    scheme='',
                    netloc='',
                    params=u.params,
                    path=u.path or '/',
                    query=u.query,
                    fragment=u.fragment
                )
            )
        # Connect to destination
        self._proxy_sock = create_connection((self.hostname, int(self.port)))

        # Wrap socket if SSL is required
        if self.is_connect:
            context = create_default_context(cafile=self.ca_file)
            self._proxy_sock = context.wrap_socket(
                sock=self._proxy_sock, server_hostname=self.hostname)
            cert = self._proxy_sock.getpeercert()
            if cert:
                self.san = cert.get('subjectAltName', [
                    ('DNS', self.hostname)])  # type:ignore

    def _transition_to_ssl(self) -> 'None':
        ssl_context = create_default_context(
            purpose=Purpose.CLIENT_AUTH, cafile=self.ca_file)
        ssl_context.verify_mode = CERT_OPTIONAL
        cert: 'str'
        pem: 'str'
        cert, pem = self.server.ca.generate_sign_cert(
            cn=self.hostname, san=self.san)
        ssl_context.load_cert_chain(certfile=cert, keyfile=pem)
        self.request = ssl_context.wrap_socket(
            sock=self.request, server_side=True)

    def do_CONNECT(self):
        self.is_connect = True
        try:
            # Connect to destination first
            self._connect_to_host()

            # If successful, let's do this!
            self.send_response(code=200, message='Connection established')
            self.end_headers()
            # self.request.sendall('%s 200 Connection established\r\n\r\n' % self.request_version)
            self._transition_to_ssl()

        except Exception as e:
            self.send_error(code=500, message=str(e))
            return

        # Reload!
        self.setup()
        self.ssl_host = f'https://{self.path}'
        self.handle_one_request()

    def do_COMMAND(self) -> 'None':
        # Is this an SSL tunnel?
        if not self.is_connect:
            try:
                # Connect to destination
                self._connect_to_host()
            except Exception as e:
                self.send_error(code=500, message=str(e))
                return
            # Extract path

        # Build request
        self.http_request_title: 'str' = \
            f'{self.command} {self.path} {self.request_version}\r\n'

        # Add headers to the request
        self.http_request_headers: 'dict[str,str]' = dict()

        for header, value in self.headers.items():
            self.http_request_headers[header] = value

        # Append message body if present to the request
        self.http_request_body = b""
        if 'Content-Length' in self.headers:
            self.http_request_body += self.rfile.read(
                int(self.headers['Content-Length']))

        # # Send it down the pipe!
        self._proxy_sock.sendall(self.build_request())

        # Parse response
        self.http_response: 'HTTPResponse' = HTTPResponse(sock=self._proxy_sock)

        self.http_response.begin()
        # Get rid of the pesky header
        del self.http_response.msg['Transfer-Encoding']

        self.http_response_title: 'str' = \
            f'{self.request_version
               } {self.http_response.status
                  } {self.http_response.reason}\r\n'

        self.http_response_headers: 'dict[str,str]' = dict()
        for header, value in self.http_response.getheaders():
            self.http_response_headers[header] = value
        self.http_response_body = self.http_response.read()

        # Let's close off the remote end
        self.http_response.close()
        self._proxy_sock.close()

        # Relay the message
        self.request.sendall(self.build_response())

    def build_http_message(self, title: 'str', headers: 'dict[str,str]', body: 'bytes') -> 'bytes':
        http_headers = ""
        for header, value in headers.items():
            http_headers += f"{header}: {value}\r\n"
        http_headers += "\r\n"  # End of headers

        return title.encode(encoding="utf-8") + \
            http_headers.encode(encoding="utf-8") + \
            body

    def build_request(self) -> 'bytes':
        return self.build_http_message(title=self.http_request_title, headers=self.http_request_headers, body=self.http_request_body)

    def build_response(self) -> 'bytes':
        return self.build_http_message(title=self.http_response_title, headers=self.http_response_headers, body=self.http_response_body)

    def __getattr__(self, item: 'str'):
        if item.startswith('do_'):
            return self.do_COMMAND

    def log_message(self, format: str, *args: 'Any') -> 'None':
        message = format % args
        logger.info("%s - - [%s] %s %s\n" %
                    (self.address_string(),
                     self.log_date_time_string(),
                     self.request_id or "",
                     message.translate(self._control_char_table)))  # type:ignore
