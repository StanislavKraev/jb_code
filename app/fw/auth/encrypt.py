# -*- coding: utf-8 -*-

# Use the system PRNG if possible
import base64
from datetime import datetime
from decimal import Decimal
import hashlib
import hmac
import os
import struct
import operator
import binascii
import time

import random

try:
    random = random.SystemRandom()
    using_sysrandom = True
except NotImplementedError:
    import warnings

    warnings.warn('A secure pseudo-random number generator is not available '
                  'on your system. Falling back to Mersenne Twister.')
    using_sysrandom = False

SECRET_KEY = os.environ.get("LO_PLATFORM_SECRET_KEY") or "drn2_k9k4)ow3h()21(IU1(dn=4d66h@54dw^*#t8)1ypm_$zg(7@45"


def is_protected_type(obj):
    """Determine if the object instance is of a protected type.

    Objects of protected types are preserved as-is when passed to
    force_text(strings_only=True).
    """
    return isinstance(obj, (int, long) + (type(None), float, Decimal,
                                          datetime.datetime, datetime.date, datetime.time))


def force_bytes(s, encoding='utf-8', strings_only=False, errors='strict'):
    # Handle the common case first for performance reasons.
    if isinstance(s, bytes):
        if encoding == 'utf-8':
            return s
        else:
            return s.decode('utf-8', errors).encode(encoding, errors)
    if strings_only and is_protected_type(s):
        return s
    if not isinstance(s, basestring):
        try:
            return bytes(s)
        except UnicodeEncodeError:
            if isinstance(s, Exception):
                # An Exception subclass containing non-ASCII data that doesn't
                # know how to print itself properly. We shouldn't raise a
                # further exception.
                return b' '.join([force_bytes(arg, encoding, strings_only,
                                              errors) for arg in s])
            return unicode(s).encode(encoding, errors)
    else:
        return s.encode(encoding, errors)


def _fast_hmac(key, msg, digest):
    """
    A trimmed down version of Python's HMAC implementation.

    This function operates on bytes.
    """
    dig1, dig2 = digest(), digest()
    if len(key) != dig1.block_size:
        raise ValueError('Key size needs to match the block_size of the digest.')
    dig1.update(key.translate(hmac.trans_36))
    dig1.update(msg)
    dig2.update(key.translate(hmac.trans_5C))
    dig2.update(dig1.digest())
    return dig2


def _bin_to_long(x):
    """
    Convert a binary string into a long integer

    This is a clever optimization for fast xor vector math
    """
    return int(binascii.hexlify(x), 16)


def _long_to_bin(x, hex_format_string):
    """
    Convert a long integer into a binary string.
    hex_format_string is like "%020x" for padding 10 characters.
    """
    return binascii.unhexlify((hex_format_string % x).encode('ascii'))


def pbkdf2(password, salt, iterations, dklen=0, digest=None):
    """
    Implements PBKDF2 as defined in RFC 2898, section 5.2

    HMAC+SHA256 is used as the default pseudo random function.

    As of 2011, 10,000 iterations was the recommended default which
    took 100ms on a 2.2Ghz Core 2 Duo. This is probably the bare
    minimum for security given 1000 iterations was recommended in
    2001. This code is very well optimized for CPython and is only
    four times slower than openssl's implementation. Look in
    django.contrib.auth.hashers for the present default.
    """
    assert iterations > 0
    if not digest:
        digest = hashlib.sha256
    password = force_bytes(password)
    salt = force_bytes(salt)
    hlen = digest().digest_size
    if not dklen:
        dklen = hlen
    if dklen > (2 ** 32 - 1) * hlen:
        raise OverflowError('dklen too big')
    l = -(-dklen // hlen)
    r = dklen - (l - 1) * hlen

    hex_format_string = "%%0%ix" % (hlen * 2)

    inner_digest_size = digest().block_size
    if len(password) > inner_digest_size:
        password = digest(password).digest()
    password += b'\x00' * (inner_digest_size - len(password))

    def F(i):
        def U():
            u = salt + struct.pack(b'>I', i)
            for j in xrange(int(iterations)):
                u = _fast_hmac(password, u, digest).digest()
                yield _bin_to_long(u)

        return _long_to_bin(reduce(operator.xor, U()), hex_format_string)

    T = [F(x) for x in range(1, l + 1)]
    return b''.join(T[:-1]) + T[-1][:r]


def get_random_string(length=12,
                      allowed_chars='abcdefghijklmnopqrstuvwxyz'
                                    'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'):
    """
    Returns a securely generated random string.

    The default length of 12 with the a-z, A-Z, 0-9 character set returns
    a 71-bit value. log_2((26+26+10)^12) =~ 71 bits
    """
    if not using_sysrandom:
        # This is ugly, and a hack, but it makes things better than
        # the alternative of predictability. This re-seeds the PRNG
        # using a value that is hard for an attacker to predict, every
        # time a random string is required. This may change the
        # properties of the chosen random sequence slightly, but this
        # is better than absolute predictability.
        random.seed(
            hashlib.sha256(
                ("%s%s%s" % (
                    random.getstate(),
                    time.time(),
                    SECRET_KEY)).encode('utf-8')
            ).digest())
    return ''.join(random.choice(allowed_chars) for i in range(length))


def encrypt_password(password, salt=None):
    salt = salt or get_random_string()
    iterations = 12000
    algorithm = "pbkdf2_sha256"
    hash = pbkdf2(password, salt, iterations, digest=hashlib.sha256)
    # noinspection PyTypeChecker
    hash = base64.b64encode(hash).decode('ascii').strip()
    return "%s$%d$%s$%s" % (algorithm, iterations, salt, hash)


def check_password(plain_password, encrypted_password):
    if '$' not in encrypted_password or len(encrypted_password.split('$')) != 4:
        return False

    algorithm, iterations, salt, hash = encrypted_password.split('$', 3)
    check_pwd = encrypt_password(plain_password, salt)
    return check_pwd == encrypted_password
