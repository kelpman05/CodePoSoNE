# From vmware/vsphere-automation-sdk-python
# https://github.com/vmware/vsphere-automation-sdk-python/blob/adee4fabfd14a20ecf7dd788c233f6dd6c0bda7b/samples/vsphere/common/sso.py#L927

"""
* *******************************************************
* SPDX-License-Identifier: MIT
* *******************************************************
*
* DISCLAIMER. THIS PROGRAM IS PROVIDED TO YOU "AS IS" WITHOUT
* WARRANTIES OR CONDITIONS OF ANY KIND, WHETHER ORAL OR WRITTEN,
* EXPRESS OR IMPLIED. THE AUTHOR SPECIFICALLY DISCLAIMS ANY IMPLIED
* WARRANTIES OR CONDITIONS OF MERCHANTABILITY, SATISFACTORY QUALITY,
* NON-INFRINGEMENT AND FITNESS FOR A PARTICULAR PURPOSE.
"""

import base64
import re

from OpenSSL import crypto

from .const import SHA256, UTF_8


def _extract_certificate(cert):
    '''
    Extract DER certificate/private key from DER/base64-ed DER/PEM string.
    @type           cert: C{str}
    @param          cert: Certificate/private key in one of three supported
                    formats.
    @rtype: C{str}
    @return: Certificate/private key in DER (binary ASN.1) format.
    '''
    if not cert:
        raise IOError('Empty certificate')
    signature = cert[0]
    # DER certificate is sequence.  ASN.1 sequence is 0x30.
    if signature == '\x30':
        return cert
    # PEM without preamble.  Base64-encoded 0x30 is 0x4D.
    if signature == '\x4D':
        return base64.b64decode(cert)
    # PEM with preamble.  Starts with '-'.
    if signature == '-':
        return base64.b64decode(re.sub('-----[A-Z ]*-----', '', cert))
    # Unknown format.
    raise IOError('Invalid certificate file format')


def _load_private_key(der_key):
    '''
    An internal helper to load private key.
    @type  der_key: C{str}
    @param der_key: The private key, in DER format.
    @rtype: crypto.privatekey
    @return: Loaded private key.
    '''

    # OpenSSL 0.9.8 does not handle correctly PKCS8 keys passed in DER format
    # (only PKCS1 keys are understood in DER format).

    # Unencrypted PKCS8, or PKCS1 for OpenSSL 1.0.1, PKCS1 for OpenSSL 0.9.8
    try:
        return crypto.load_privatekey(crypto.FILETYPE_ASN1, der_key, '')
    except (crypto.Error, ValueError):
        pass
    # Unencrypted PKCS8 for OpenSSL 0.9.8, and PKCS1, just in case...
    for key_type in ('PRIVATE KEY', 'RSA PRIVATE KEY'):
        try:
            return crypto.load_privatekey(
                crypto.FILETYPE_PEM,
                '-----BEGIN {}-----\n{}-----END {}-----\n'.format(
                    key_type,
                    base64.encodebytes(der_key).decode(UTF_8),
                    key_type,
                ),
                b'',
            )
        except (crypto.Error, ValueError):
            pass
    # We could try 'ENCRYPTED PRIVATE KEY' here - but we do not know
    # passphrase.
    raise ValueError('invalid private key format or encrypted key')


def sign(private_key, data, digest=SHA256):
    '''
    An internal helper method to sign the 'data' with the 'private_key'.
    @type  private_key: C{str}
    @param private_key: The private key used to sign the 'data', in one of
                        supported formats.
    @type         data: C{str}
    @param        data: The data that needs to be signed.
    @type       digest: C{str}
    @param      digest: Digest is a str naming a supported message digest type,
                        for example 'sha256'.
    @rtype: C{str}
    @return: Signed string.
    '''
    # Convert private key in arbitrary format into DER (DER is binary format
    # so we get rid of \n / \r\n differences, and line breaks in PEM).
    if isinstance(private_key, crypto.PKey):
        pkey = private_key
    else:
        pkey = _load_private_key(_extract_certificate(private_key))

    return crypto.sign(pkey, data, digest)
