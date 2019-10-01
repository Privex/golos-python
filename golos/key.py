# -*- coding: utf-8 -*-
"""

"""
from pprint import pprint
import json

import hashlib
from binascii import hexlify, unhexlify
from typing import List, Union, Dict

from graphenebase.account import PrivateKey, PublicKey

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
            s = hashlib.sha256(b).digest()
            k = hexlify(s).decode('ascii')
            pk = PrivateKey(wif = k, prefix = Key.prefix)
            keys["private"][role] = str(pk)
            keys["public"][role] = str(pk.pubkey)
            pk2 = PublicKey(keys["public"][role], prefix=Key.prefix)  # Для игр
        
        return keys
    
    @staticmethod
    def get_public(wif: Union[str, PrivateKey, Base58]) -> str:
        """
        Get the prefixed public key for a given WIF private key.

            >>> Key.get_public('5Jq19TeeVmGrBFnu32oxfxQMiipnSCKmwW7fZGUVLAoqsKJ9JwP')
            'GLS7qHue1h2eWV8M7WKtb6F8dbhKfEFvLVy9JqvSTHBBEM5JMdsmh'

        :param str wif: A string private key in WIF format
        :return str pubkey: The prefixed public key generated from the given ``wif``
        """
        pk = PrivateKey(wif, prefix=Key.prefix)
        return str(pk.pubkey)
    
    @staticmethod
    def is_key(wif, gls) -> bool:
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

        :param str wif: The private key, as a WIF string, to compare against the public key ``gls``
        :param str gls: The public key, as a prefixed string address, to compare against the private key ``wif``
        :return bool key_matches: ``True`` if ``wif``'s public key matches ``gls`` - otherwise ``False``
        """
        pk = PrivateKey(wif, prefix=Key.prefix)
        if str(pk.pubkey) == gls:
            return True
        return False


if __name__ == '__main__':
    
    pass
