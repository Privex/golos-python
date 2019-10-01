# -*- coding: utf-8 -*-
"""

"""
from pprint import pprint
import json

import hashlib
from binascii import hexlify, unhexlify
from typing import List, Union, Dict

import ecdsa
from .base58 import gphBase58CheckEncode, base58CheckEncode, base58CheckDecode, gphBase58CheckDecode
from golos.base58 import Base58
from .storage import prefix


class Key:
    """
    ``Key`` is a static class which contains several static methods for working with public/private keys, as well
    as key generation based on a username + password.
    
    See the PyDoc blocks on the class methods :py:meth:`.get_keys` :py:meth:`.get_public` and :py:meth:`.is_key`
    
    """
    roles: List[str] = ["posting", "active", "memo", "owner"]
    """A list of roles to generate keys for, used by :py:meth:`.get_keys`"""
    
    prefix: str = prefix
    """The public key prefix used by the network, e.g. ``GLS``"""
    
    @staticmethod
    def get_keys(account: str, password: str) -> Dict[str, Union[str, Dict[str, str]]]:
        """
        Generates a dictionary containing public/private keys for each **role** of an account (e.g. ``active``)
        based on the given ``account`` (username) and ``password``

        Example:

            >>> acc = Key.get_keys('someguy123', 'example')
            >>> acc['private']['active']
            5KME2a7DBdGBdpAwLC4tGmJ8mSz9HgZkcMtKc8rkADn6cLZyvPc
            >>> acc['public']['active']
            GLS7LjcmXF4mf9z3MNgcceSvMG8oezEtGhcL4yAXpJWFZxdX47ET7


        :param str account: The username to generate role keys for, e.g. ``someguy123``
        :param str password: The string password to use for generating the keys
        :return dict acc_keys: ``dict(login:str, password:str, private:Dict[str,str], public:Dict[str,str])``

        First layer of returned dict::

            dict(login:str, password:str, private:Dict[str,str], public:Dict[str,str])

        Second layer (dict keys ``private`` and ``public``)::

            dict(posting:str, active:str, memo:str, owner:str)

        """
        keys = {"login": account, "password": password, "private": {}, "public": {}}
        
        for role in Key.roles:
            
            b = bytes(account + role + password, 'utf8')
            secret = hashlib.sha256(b).digest()
            keys["private"][role] = Key.get_private_from_secret(secret)
            keys["public"][role] = Key.get_public_from_secret(secret)
        
        return keys

    @staticmethod
    def get_private_from_secret(secret: bytes) -> str:
        k = hexlify(secret).decode('ascii')  # repr(b58) Gives the hex representation of the Graphene private key.
        private_key = base58CheckEncode(0x80, k)
        return str(private_key)

    @staticmethod
    def get_public_from_secret(secret: bytes) -> str:
        """
        Converts an ECDSA formatted private key into it's matching public key with prefix
        
            >>> wif = '5Jq19TeeVmGrBFnu32oxfxQMiipnSCKmwW7fZGUVLAoqsKJ9JwP'
            >>> secret = unhexlify(base58CheckDecode(str(wif)))
            >>> Key.get_public_from_secret(secret)
            'GLS7qHue1h2eWV8M7WKtb6F8dbhKfEFvLVy9JqvSTHBBEM5JMdsmh'
            
        """
        order = ecdsa.SigningKey.from_string(secret, curve=ecdsa.SECP256k1).curve.generator.order()
        point = ecdsa.SigningKey.from_string(secret, curve=ecdsa.SECP256k1).verifying_key.pubkey.point
        x_str = ecdsa.util.number_to_string(point.x(), order)
        compressed = hexlify(chr(2 + (point.y() & 1)).encode("ascii") + x_str).decode("ascii")
        public_key = Key.prefix + gphBase58CheckEncode(compressed)
        return str(public_key)

    @staticmethod
    def get_public_from_private(wif) -> str:
        """
        Get the prefixed public key for a given WIF private key.

            >>> Key.get_public_from_private('5Jq19TeeVmGrBFnu32oxfxQMiipnSCKmwW7fZGUVLAoqsKJ9JwP')
            'GLS7qHue1h2eWV8M7WKtb6F8dbhKfEFvLVy9JqvSTHBBEM5JMdsmh'

        :param str wif: A string private key in WIF format
        :return str pubkey: The prefixed public key generated from the given ``wif``
        """
        secret = unhexlify(base58CheckDecode(str(wif)))  # Преобразование из приватного ключа
        public_key = Key.get_public_from_secret(secret)
        return str(public_key)
    
    @staticmethod
    def is_key(wif, public) -> bool:
        """
        Check if a private key ``wif`` matches a public key ``gls``

        Example:

            >>> kp1 = '5Jq19TeeVmGrBFnu32oxfxQMiipnSCKmwW7fZGUVLAoqsKJ9JwP',
            ... 	  'GLS7qHue1h2eWV8M7WKtb6F8dbhKfEFvLVy9JqvSTHBBEM5JMdsmh'
            >>>
            >>> kp2 = '5KPQo2iNeACYagW5qAsgNpFxDDuwuArCCG8PvU6FKTMcD5LmhzJ',
            ...       'GLS8G7rgqhPUbyzYVYWb8BPcHtpgLDmJYooHmHPbaLaH7cdywsdwm'
            >>>
            >>> Key.is_key(kp1[0], kp1[1])   # Compare keypair 1's private key against it's own public key
            True
            >>> Key.is_key(kp1[0], kp2[1])   # Compare keypair 1's private key against keypair 2's public key
            False

        :param str wif: The private key, as a WIF string, to compare against the public key ``public``
        :param str public: The public key, as a prefixed string address, to compare against the private key ``wif``
        :return bool key_matches: ``True`` if ``wif``'s public key matches ``public`` - otherwise ``False``
        """
        res = True if public == Key.get_public_from_private(wif) else False
        return res


if __name__ == '__main__':
    
    pass
