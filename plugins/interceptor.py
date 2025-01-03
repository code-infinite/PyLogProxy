""" Interceptor plugin for log request """

from gzip import BadGzipFile, GzipFile
from io import BytesIO
from typing import TYPE_CHECKING
from zlib import compressobj as zlib_compressobj
from zlib import decompressobj as zlib_decompressobj
from zlib import error as zlib_error

from brotli import compress as brotli_compress  # type:ignore
from brotli import decompress as brotli_decompress  # type:ignore
from brotli import error as brotli_error  # type:ignore

if TYPE_CHECKING:

    from base.handlers.request_handler import ProxyRequestHandler
    from base.server.proxy_server import BaseProxyServer

__author__ = 'Rushirajsinh Chudasama'
__copyright__ = 'Copyright 2025, PyLogProxy Project'
__credits__ = ['Rushirajsinh Chudasama']

__license__ = 'MIT'
__status__ = 'Development'

__all__ = [
    'RequestInterceptorPlugin',
    'ResponseInterceptorPlugin',
    'InvalidInterceptorPluginException'
]


class InterceptorPlugin(object):

    def __init__(self, server: 'BaseProxyServer', http_message_handler: 'ProxyRequestHandler') -> 'None':
        self.server = server
        self.http_message_handler = http_message_handler

    def decompress_data(self, body: 'bytes', content_encoding: 'str') -> 'tuple[bool, bytes, str, str]':
        # Check the Content-Encoding header and decompress accordingly
        decompressed_data: 'bytes' = b""
        decompression_error: 'str' = ""
        decompression_warning: 'str' = ""
        decompression_success = False
        if content_encoding == 'gzip':
            try:
                with GzipFile(fileobj=BytesIO(body)) as f:
                    decompressed_data = f.read()
                decompression_success = True
            except (BadGzipFile, IOError) as e:
                decompression_error = f"Error decompressing the data: {e}"
            except EOFError:
                decompression_error = f"Error: Reached the end of the file unexpectedly while reading."
            except Exception as e:
                decompression_error = f"An unexpected error occurred: {e}"

        elif content_encoding == 'deflate':
            try:
                decompressor = zlib_decompressobj()
                decompressed_data = decompressor.decompress(body)
                if decompressor.unused_data:
                    decompression_warning = "Warning: Some unused data was left over."
                decompression_success = True
            except zlib_error as e:
                # Handle decompression errors
                decompression_error = f"Decompression failed: {e}"
            except ValueError as e:
                # Handle invalid data input, if any
                decompression_error = f"Invalid input data: {e}"
            except Exception as e:
                # Catch all other exceptions
                decompression_error = f"An unexpected error occurred: {e}"

        elif content_encoding == 'br':
            try:
                decompressed_data = brotli_decompress(  # type:ignore
                    body)
                decompression_success = True
            except brotli_error as e:  # type:ignore
                # Handle decompression-specific errors
                decompression_error = f"Decompression failed: {e}"
            except TypeError as e:
                # Handle invalid input types (e.g., non-bytes input)
                decompression_error = f"Invalid input data: {e}"
            except Exception as e:
                # Handle any other unexpected errors
                decompression_error = f"An unexpected error occurred: {e}"

        return decompression_success, decompressed_data, decompression_error, decompression_warning  # type:ignore

    def compress_data(self, body: 'bytes', content_encoding: 'str') -> 'tuple[bool, bytes, str, str]':
        # Check the Content-Encoding header and decompress accordingly
        compressed_data: 'bytes' = b""
        compression_error: 'str' = ""
        compression_warning: 'str' = ""
        compression_success = False
        if content_encoding == 'gzip':
            try:
                out_file = BytesIO()
                with GzipFile(fileobj=out_file, mode="wb") as f:
                    f.write(data=body)
                compressed_data = out_file.getvalue()
                compression_success = True
            except (BadGzipFile, IOError) as e:
                compression_error = f"Error compressing the data: {e}"
            except Exception as e:
                compression_error = f"An unexpected error occurred: {e}"

        elif content_encoding == 'deflate':
            try:
                compressor = zlib_compressobj()
                compressed_data = compressor.compress(body)
                compression_success = True
            except zlib_error as e:
                # Handle decompression errors
                compression_error = f"Compression failed: {e}"
            except ValueError as e:
                # Handle invalid data input, if any
                compression_error = f"Invalid input data: {e}"
            except Exception as e:
                # Catch all other exceptions
                compression_error = f"An unexpected error occurred: {e}"

        elif content_encoding == 'br':
            try:
                compressed_data = brotli_compress(  # type:ignore
                    string=body)
                compression_success = True
            except brotli_error as e:  # type:ignore
                # Handle decompression-specific errors
                compression_error = f"Compression failed: {e}"
            except TypeError as e:
                # Handle invalid input types (e.g., non-bytes input)
                compression_error = f"Invalid input data: {e}"
            except Exception as e:
                # Handle any other unexpected errors
                compression_error = f"An unexpected error occurred: {e}"

        return compression_success, compressed_data, compression_error, compression_warning  # type:ignore

    def modify_response(self, http_response: 'bytes') -> 'bytes':
        # process response here
        return http_response


class RequestInterceptorPlugin(InterceptorPlugin):

    def process_request(self) -> 'None':
        pass


class ResponseInterceptorPlugin(InterceptorPlugin):

    def process_response(self) -> 'None':
        pass


class InvalidInterceptorPluginException(Exception):
    pass


class DebugInterceptor(RequestInterceptorPlugin, ResponseInterceptorPlugin):

    def process_request(self) -> 'None':
        self.http_message_handler.logger.info("\n\n")
        self.http_message_handler.logger.info(str(self.http_message_handler.http_request_title))
        self.http_message_handler.logger.info(str(self.http_message_handler.http_request_headers) + "\n\n")
        self.http_message_handler.logger.info(self.http_message_handler.http_request_body)
        self.http_message_handler.logger.info("\n\n")

    def process_response(self) -> 'None':
        self.http_message_handler.logger.info(str(self.http_message_handler.http_response_title))
        self.http_message_handler.logger.info(str(self.http_message_handler.http_response_headers) + "\n\n")
        content_encoding: 'str' = self.http_message_handler.http_response_headers.get('Content-Encoding', '')
        if content_encoding in ['gzip', 'deflate', 'br']:
            decompression_success, http_response_body, \
                decompression_error, decompression_warning = \
                self.decompress_data(body=self.http_message_handler.http_response_body,
                                     content_encoding=content_encoding)
            if decompression_success:
                self.http_message_handler.logger.debug(f"Decompressed ({content_encoding}):\n {http_response_body}\n\n")
            else:
                self.http_message_handler.logger.error(decompression_error)
            if decompression_warning:
                self.http_message_handler.logger.warning(decompression_warning)

            self.modify_response(http_response=http_response_body)

            compression_success, self.http_message_handler.http_response_body, \
                compression_error, compression_warning = \
                self.compress_data(body=http_response_body, content_encoding=content_encoding)
            if compression_success:
                self.http_message_handler.logger.debug(
                    f"Compressed ({content_encoding}):\n {self.http_message_handler.http_response_body}\n\n")
            else:
                self.http_message_handler.logger.error(compression_error)
            if compression_warning:
                self.http_message_handler.logger.warning(compression_warning)

            self.http_message_handler.http_response_headers['Content-Length'] = str(len(
                self.http_message_handler.http_response_body))

        else:
            self.http_message_handler.logger.warning(f"No compression or unsupported encoding. - {content_encoding}")
            self.http_message_handler.logger.debug(self.http_message_handler.http_response_body)
