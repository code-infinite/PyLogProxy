from logging import StreamHandler, getLogger
from sys import stderr, stdout
from typing import TYPE_CHECKING

from toml import load

if TYPE_CHECKING:
    from typing import Any


ssl_config: 'dict[str, dict[str,Any]]' = load("config/ssl_config.toml")

try:
    ssl_certificate: 'dict[str,Any]' = ssl_config.pop("ssl_certificate")
    ssl_private_key: 'dict[str,Any]' = ssl_config.pop("ssl_private_key")
    ssl_digest: 'dict[str,Any]' = ssl_config.pop("ssl_digest")
    ssl_certificate_file: 'dict[str,Any]' = ssl_config.pop("certificate")
    del ssl_config
except KeyError as key_error:
    stderr.write(f"SSL config is missing section {key_error}")

app_config: 'dict[str, dict[str,Any]]' = load("config/app_config.toml")

try:
    app: 'dict[str,Any]' = app_config.pop("app")
    app_log: 'dict[str,str]' = app_config['log'].pop("app")
    request_log: 'dict[str,Any]' = app_config['log'].pop("request")
    cache: 'dict[str,Any]' = app_config.pop("cache")
    del app_config
except KeyError as key_error:
    stderr.write(f"Application config is missing section {key_error}")


logger = getLogger("Root")
logger.setLevel(app_log['level'].upper())  # type:ignore
sh = StreamHandler(stdout)
logger.addHandler(sh)
