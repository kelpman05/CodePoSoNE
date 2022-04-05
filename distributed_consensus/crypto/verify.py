import base64

from OpenSSL import crypto

from .const import SHA256, UTF_8
from .sign import _extract_certificate


def flattern(args):
    ans = []
    for a in args:
        if isinstance(a, (list, tuple)):
            ans.extend(flattern(a))
        else:
            ans.append(a)
    return ans


def _load_public_key(der_key):
    '''
    An internal helper to load public key.
    @type  der_key: C{str}
    @param der_key: The private key, in DER format.
    @rtype: crypto.PKey
    @return: Loaded public key.
    '''

    # OpenSSL 0.9.8 does not handle correctly PKCS8 keys passed in DER format
    # (only PKCS1 keys are understood in DER format).

    # Unencrypted PKCS8, or PKCS1 for OpenSSL 1.0.1, PKCS1 for OpenSSL 0.9.8
    try:
        return crypto.load_publickey(crypto.FILETYPE_ASN1, der_key)
    except (crypto.Error, ValueError):
        pass
    # Unencrypted PKCS8 for OpenSSL 0.9.8, and PKCS1, just in case...
    for key_type in ('PUBLIC KEY', 'RSA PUBLIC KEY'):
        try:
            return crypto.load_publickey(
                crypto.FILETYPE_PEM,
                '-----BEGIN {}-----\n{}-----END {}-----\n'.format(
                    key_type,
                    base64.encodestring(der_key).decode(UTF_8),
                    key_type,
                ),
            )
        except (crypto.Error, ValueError):
            pass
    raise ValueError('invalid public key format')


def verify(public_key, signature, data: bytes, digest=SHA256):
    if isinstance(public_key, crypto.PKey):
        pkey = public_key
    else:
        pkey = _load_public_key(_extract_certificate(public_key))

    cert = crypto.X509()
    cert.set_pubkey(pkey)

    try:
        crypto.verify(cert, signature, data, digest)
    except crypto.Error as exc:
        return False
        # flattern(exc.args)
        #if 'bad signature' in flattern(exc.args):
            #return False
        #else:
            #raise
    return True
