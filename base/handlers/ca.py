""" Handle SSL Certificates management"""

from os import makedirs, path
from random import randint
from tempfile import gettempdir

from OpenSSL.crypto import (FILETYPE_PEM, X509, PKey, X509Extension, X509Req,
                            dump_certificate, dump_privatekey,
                            load_certificate, load_privatekey)

from base import (cache, ssl_certificate, ssl_certificate_file, ssl_digest,
                  ssl_private_key)

__author__ = 'Rushirajsinh Chudasama'
__copyright__ = 'Copyright 2025, PyLogProxy Project'
__credits__ = ['Rushirajsinh Chudasama']

__license__ = 'MIT'
__status__ = 'Development'

__all__ = [
    'CertificateAuthority'
]


class CertificateAuthority:

    """ Class to handle Certificate Authority """

    def __init__(self, cache_dir: 'str' = cache['dir'] or f"{gettempdir()}/pylogproxy") -> 'None':
        makedirs(name=cache_dir, exist_ok=True)
        self.pkey_file = f"{cache_dir}/{ssl_certificate_file['private_key_name']}"
        self.crt_file = f"{cache_dir}/{ssl_certificate_file['certificate_name']}"
        self.cache_dir = cache_dir

        if not path.exists(path=self.pkey_file):
            self._generate_ca()
        else:
            self._read_pkey()

    def _generate_ca(self) -> 'None':
        # Generate key
        self.key = PKey()
        self.key.generate_key(type=ssl_private_key['key_algorithm'], bits=ssl_private_key['key_size'])

        # Generate certificate
        self.cert = X509()
        self.cert.set_version(version=2)
        self.cert.set_serial_number(serial=1)

        subject = self.cert.get_subject()
        subject.C = ssl_certificate["country"]
        subject.ST = ssl_certificate["state"]
        subject.L = ssl_certificate["locality"]
        subject.O = ssl_certificate["organization"]
        subject.OU = ssl_certificate["organizational_unit"]
        subject.CN = ssl_certificate["common_name"]
        subject.emailAddress = ssl_certificate["email"]

        self.cert.set_issuer(issuer=subject)

        self.cert.gmtime_adj_notBefore(amount=0)
        self.cert.gmtime_adj_notAfter(amount=ssl_certificate['validity']['validity_seconds'])

        self.cert.set_pubkey(pkey=self.key)

        self.cert.add_extensions(extensions=[
            X509Extension(type_name=b"basicConstraints",
                          critical=True, value=b"CA:TRUE, pathlen:0"),
            X509Extension(type_name=b"keyUsage", critical=True,
                          value=b"keyCertSign, cRLSign"),
            X509Extension(type_name=b"subjectKeyIdentifier",
                          critical=False, value=b"hash", subject=self.cert),
        ])
        self.cert.sign(pkey=self.key, digest=ssl_digest['digest'])

        with open(file=self.pkey_file, mode='wb') as f:
            f.write(dump_privatekey(type=FILETYPE_PEM, pkey=self.key))

        with open(file=self.crt_file, mode='wb') as f:
            f.write(dump_certificate(type=FILETYPE_PEM, cert=self.cert))

    def _read_pkey(self) -> None:
        with open(file=self.crt_file, mode='rb') as f:
            self.cert = load_certificate(type=FILETYPE_PEM, buffer=f.read())

        with open(file=self.pkey_file, mode='rb') as f:
            self.key = load_privatekey(type=FILETYPE_PEM, buffer=f.read())

    def generate_sign_cert(self, cn: 'str', san: 'list[tuple[str,str]]') -> 'tuple[str,str]':
        cnp: 'str' = path.sep.join([self.cache_dir, '.pylogp_%s.pem' % cn])
        cnc: 'str' = path.sep.join(
            [self.cache_dir, '.pycrt_%s.pem' % cn])
        if not path.exists(path=cnp):

            san_list: 'list[str]' = []
            for entry in san:
                if len(entry) > 0 and entry[0] == "DNS":
                    san_list.append(f"{entry[0]}:{entry[1]}")

            # create private key
            key = PKey()
            key.generate_key(type=ssl_private_key['key_algorithm'], bits=ssl_private_key['key_size'])

            # Generate CSR
            csr = X509Req()
            csr.get_subject().CN = cn
            csr.set_pubkey(pkey=key)
            csr.sign(pkey=key, digest=ssl_digest['digest'])

            # Sign CSR
            cert = X509()
            cert.set_serial_number(
                serial=randint(1000000000, 9999999999))
            cert.set_subject(subject=csr.get_subject())
            cert.set_issuer(issuer=self.cert.get_subject())
            cert.set_version(version=2)
            cert.gmtime_adj_notBefore(amount=0)
            cert.gmtime_adj_notAfter(amount=31536000)
            cert.set_pubkey(pkey=csr.get_pubkey())
            cert.add_extensions(extensions=[
                X509Extension(type_name=b"subjectAltName", critical=False,
                              value=",".join(san_list).encode('utf-8')),
            ])
            cert.sign(pkey=self.key, digest=ssl_digest['digest'])

            with open(file=cnc, mode='wb') as f:
                f.write(dump_certificate(type=FILETYPE_PEM, cert=cert))

            with open(file=cnp, mode='wb') as f:
                f.write(dump_privatekey(type=FILETYPE_PEM, pkey=key))

        return cnc, cnp
