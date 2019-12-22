"""
This is the main module for the GOLOS library, containing the class :class:`.Api` which is the high-level class
to be used when interacting with python-golos.

Copyright::

    +===================================================+
    |                 © 2019 Privex Inc.                |
    |               https://www.privex.io               |
    +===================================================+
    |                                                   |
    |        Privex's Golos Library                     |
    |        License: X11/MIT                           |
    |                                                   |
    |        Core Developer(s):                         |
    |                                                   |
    |          (+)  Chris (@someguy123) [Privex]        |
    |                                                   |
    +===================================================+

    Privex's Golos Python Library
    Copyright (c) 2019    Privex Inc. ( https://www.privex.io )

    Permission is hereby granted, free of charge, to any person obtaining a copy of
    this software and associated documentation files (the "Software"), to deal in
    the Software without restriction, including without limitation the rights to use,
    copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the
    Software, and to permit persons to whom the Software is furnished to do so,
    subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
    INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
    PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
    OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
    SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


"""
# -*- coding: utf-8 -*-
import hashlib
import json
import logging
import math
from binascii import unhexlify
from datetime import datetime
from decimal import Decimal, ROUND_DOWN
from pprint import pprint
from time import time
from typing import Union, List, Tuple, Dict

from privex.helpers import dec_round, r_cache, retry_on_err

from golos.extras import dict_sort, new_node_on_err
from .exceptions import TransactionNotFound, GolosException
from .broadcast import Tx
from .key import Key
from .storage import time_format, asset_precision, rus_d, rus_list, asset_account_keys
from .ws_client import WsClient

log = logging.getLogger(__name__)


Number = Union[Decimal, float, int, str]
"""
``Number`` is a shorthand type alias to represent numbers in various types - which can be 
either ``Decimal``, ``float``, ``int``, or ``str``
"""

DEFAULT_ASSET = 'GOLOS'
"""
The primary asset symbol of the current blockchain. Used as the default ``asset`` for some operations if not specified,
while also obligatory for power up transactions to avoid user error. 
"""


class Api:
    """
    Main class for ``golos-python`` - wraps :class:`.ws_client` and provides many helper methods for interacting
    with the GOLOS blockchain, such as :py:meth:`.get_accounts` and :py:meth:`.transfer`
    
    **Official Repo:** https://github.com/Privex/golos-python

    **Official PyPi Package Name:** ``golos-python``
    
    **Basic Usage:**

        >>> from golos import Api
        >>> golos = Api()
        >>> acc = golos.get_accounts(['someguy123'])
        >>> acc[0]['owner']
        'someguy123'
        >>> wit = golos.get_witness_by_account('someguy123')
        >>> wit['url']
        'https://golos.io/ru--delegaty/@someguy123/delegat-someguy123'
    
    
    """
    
    rpc: WsClient
    key: Key
    broadcast: Tx
    asset_precision: Dict[str, int]
    STEEMIT_BANDWIDTH_PRECISION: int
    
    MAX_RETRIES = 5
    RETRY_DELAY = 1
    
    def __init__(self, nodes: Union[List[str], str] = None, **kwargs):
        """
        Constructor for Privex's GOLOS wrapper class. No arguments are required, unless you want to override defaults.

        **Basic Usage:**

        Use default nodes list and settings:

            >>> golos = Api()

        Use only this specific node:

            >>> golos = Api(nodes='wss://golosd.privex.io')

        Use a list of nodes, and enable more verbose logging from :class:`.WsClient`

            >>> nodes = ['wss://golosd.privex.io', 'wss://api.golos.blckchnd.com/ws']
            >>> golos = Api(nodes=nodes, report=True)

        Making basic API calls:

            >>> acc = golos.get_accounts(['someguy123'])
            >>> acc[0]['owner']
            'someguy123'
            >>> wit = golos.get_witness_by_account('someguy123')
            >>> wit['url']
            'https://golos.io/ru--delegaty/@someguy123/delegat-someguy123'


        :param list|str nodes: A list / singular ``str`` GOLOS node(s) formatted like such: ``wss://golosd.privex.io``
        :param bool report: (**KWARG**) If ``True`` - enables more verbose logging from :class:`.WsClient`
        :param kwargs: Any additional keyword arguments (will be forwarded to :class:`.WsClient`'s constructor)

        """
        log.debug('connect b4 GOLOS')
        # Пользуемся своими нодами или новыми
        if nodes:
            self.rpc = WsClient(nodes=nodes, **kwargs)
        else:
            self.rpc = WsClient(**kwargs)

        log.debug('get config GOLOS')
        config_golos = self.rpc.call('get_config')
        self.STEEMIT_BANDWIDTH_PRECISION = int(config_golos["STEEMIT_BANDWIDTH_PRECISION"])

        chain_properties = self.rpc.call('get_chain_properties')
        self.account_creation_fee = chain_properties["account_creation_fee"]
        self.create_account_min_golos_fee = chain_properties["create_account_min_golos_fee"]
        self.create_account_min_delegation = chain_properties["create_account_min_delegation"]
        # "account_creation_fee": "1.000 GOLOS",
        # "create_account_min_golos_fee": "0.030 GOLOS",
        # "create_account_min_delegation": "0.150 GOLOS",
        self.create_account_max_delegation = "33333.333333 GEST"  # aka ~10 Golos Power

        self.rus_d = rus_d
        self.asset_precision = asset_precision

        self.broadcast = Tx(self.rpc)
        self.finalizeOp = self.broadcast.finalizeOp

        self.key = Key()

        log.debug('complite')

    @property
    @r_cache('golos:chain_props', cache_time=30)
    @new_node_on_err(max_retries=MAX_RETRIES, delay=RETRY_DELAY)
    def chain_properties(self) -> dict:
        """
        This property loads and caches the chain properties for up to 30 seconds, avoiding constant
        un-necessary requests for the chain properties.
        
        :return dict props: A dictionary of chain properties
        """
        props = self.get_chain_properties()
        if not props:
            log.debug('error in global data')
            raise GolosException('Error obtaining chain props...')
        return props

    @property
    @r_cache('golos:dyn_glob_props', cache_time=30)
    @new_node_on_err(max_retries=MAX_RETRIES, delay=RETRY_DELAY)
    def dynamic_global_properties(self) -> dict:
        """
        This property loads and caches the dynamic global properties for up to 30 seconds, avoiding constant
        un-necessary requests for the dynamic global properties.

        :return dict props: A dictionary of dynamic global properties
        """
        props = self.get_dynamic_global_properties()
        if not props:
            log.debug('error in global data')
            raise GolosException('Error obtaining dynamic global props using RPC node {}...'.format(self.rpc.url))
        return props
    
    def get_transaction_hex(self, tx: dict, remove_sigs=False) -> str:
        """
        Get the string hexadecimal representation of a ``dict`` transaction object.
        
        **Example Usage**:
        
            >>> tx = {
            ...     'ref_block_num': 27979, 'ref_block_prefix': 3018856747, 'expiration': '2019-10-01T12:50:00',
            ...     'operations': [
            ...         ['transfer',
            ...          {'from': 'someguy123', 'to': 'ksantoprotein', 'amount': '0.100 GOLOS', 'memo': 'testing'}]
            ...     ],
            ...     'extensions': [], 'signatures': []
            ... }
            >>> Api().get_transaction_hex(tx)
            '4b6d2b19f0b3784b935d01020a736f6d656775793132330d6b73616e746f70726f7465696e640000000000000003474f4c4f53
             00000774657374696e6700'

        :param dict tx: A transaction as a ``dict`` in the form:
                        ``dict(ref_block_num, ref_block_prefix, expiration, operations, extensions, signatures)``
        :param bool remove_sigs: (Default: ``False``) Replace the ``signatures`` key with ``[]`` (for TXID generation)
        :return str txhex: The hexadecimal representation of the transaction
        """
        tx = dict(tx)
        if remove_sigs:
            tx['signatures'] = []
        txhex = self.rpc.call('get_transaction_hex', tx)
        return str(txhex)
    
    def get_transaction_id(self, tx: dict) -> str:
        """
        Calculate the TXID for a transaction in the ``dict`` form:
        
        ``dict(ref_block_num, ref_block_prefix, expiration, operations, extensions, signatures)``
        
        
            >>> tx = {
            ...     'ref_block_num': 27979, 'ref_block_prefix': 3018856747, 'expiration': '2019-10-01T12:50:00',
            ...     'operations': [
            ...         ['transfer',
            ...          {'from': 'someguy123', 'to': 'ksantoprotein', 'amount': '0.100 GOLOS', 'memo': 'testing'}]
            ...     ],
            ...     'extensions': [], 'signatures': []
            ... }
            >>> Api().get_transaction_id(tx)
            'c901c52daf57b60242d9d7be67f790e023cf2780'
        
        :param dict tx: A transaction as a ``dict`` in the form:
                        ``dict(ref_block_num, ref_block_prefix, expiration, operations, extensions, signatures)``
        :return str txid: The calculated transaction ID for the given transaction
        """
        txhex = self.get_transaction_hex(tx, remove_sigs=True)
        m = hashlib.sha256()
        m.update(unhexlify(txhex))
        txhash = m.hexdigest()
        
        return txhash[:40]

    @new_node_on_err(max_retries=MAX_RETRIES, delay=RETRY_DELAY, fail_on=[KeyboardInterrupt, TransactionNotFound])
    def get_transaction(self, txid: str) -> dict:
        """
        Lookup the transaction ID ``txid`` and return it's matching transaction as a ``dict``
        
        **Example usage**:
        
            >>> Api().get_transaction('c901c52daf57b60242d9d7be67f790e023cf2780')
            {'ref_block_num': 27979, 'ref_block_prefix': 3018856747, 'expiration': '2019-10-01T12:50:00',
             'operations': [['transfer',
                {'from': 'someguy123', 'to': 'ksantoprotein', 'amount': '0.100 GOLOS', 'memo': 'testing'}
              ]],
              'extensions': [],
              'signatures': ['1f1a0212f7b9fe263acaeadf1ec127000dc234c413b543e3c268d251e...']
            }
        
        :param str txid: A string hex transaction ID to lookup
        :raises TransactionNotFound: When the transaction ID could not be found on the blockchain.
        :return dict tx: The matching transaction as a ``dict``
        """
        return self.rpc.call('get_transaction', txid)
    
    def find_op_transaction(self, op: dict, ignore_keys: list = None) -> dict:
        """
        Locate and return the full transaction from the blockchain based on a ``dict`` operation (``op``)
        
        The operation dictionary must contain at least ``block``, as well as all of the operation keys that
        would be found on the blockchain, with the values being the same type as they would be on the blockchain.
        
        **Example usage**:
        
            >>> op = {'from':  'someguy123', 'to': 'ksantoprotein', 'amount': '0.100 GOLOS', 'memo': 'testing',
            ...       'number': 127287, 'block': 30895436, 'timestamp': '2019-10-01T12:49:00', 'type_op': 'transfer'}
            >>> Api().find_op_transaction(op)
            {'ref_block_num': 27979, 'ref_block_prefix': 3018856747, 'expiration': '2019-10-01T12:50:00',
             'operations': [['transfer',
                {'from': 'someguy123', 'to': 'ksantoprotein', 'amount': '0.100 GOLOS', 'memo': 'testing'}
              ]],
              'extensions': [],
              'signatures': ['1f1a0212f7b9fe263acaeadf1ec127000dc234c413b543e3c268d251e...']
            }


        :param dict op: An operation as a ``dict``, containing the key ``block``, and any operation keys to match
        :param list ignore_keys: (Optional) Additional dict keys to remove from ``op``
        :raises TransactionNotFound: When a matching transaction could not be found on the blockchain.
        :return dict tx: The full transaction found on the blockchain as a ``dict``
        
        A returned transaction is generally formatted like such::
        
            dict(ref_block_num: int, ref_block_prefix: int, expiration: str, operations: list,
                 extensions: list, signatures: list)
        
        
        """
        ignore_keys = [] if not ignore_keys else ignore_keys
        ignore_keys += ['number', 'block', 'timestamp', 'type_op']
        
        orig_tx = dict(op)
        if 'block' not in orig_tx:
            raise AttributeError("Error: find_transaction requires that 'op' contains the key 'block'")
        
        # Filter out any dict keys which don't exist on blockchain transactions, so we can compare the passed TX
        # to TXs inside of a block.
        clean_tx = dict(op)
        clean_tx = {k: v for k, v in clean_tx.items() if k not in ignore_keys}

        # Load the block specified in the original TX, and search for a matching transaction.
        block = self.get_block(int(orig_tx['block']))
        for t in block['transactions']:
            for op in t['operations']:
                if 'type_op' in orig_tx and op[0] != orig_tx['type_op']:
                    continue
                tx_op = dict_sort(op[1])
                orig_op = dict_sort(clean_tx)
                if tx_op == orig_op:
                    return t
        
        raise TransactionNotFound(f'Transaction could not be found: {str(orig_tx)}')

    # ----- BROADCAST ----- #

    def vote(self, url, weight, voters, wif):

        # weight = -10000..10000
        # voters = list

        author, permlink = self.resolve_url(url)
        if not permlink:
            log.debug('error url')
            return False

        ops = []
        for voter in voters:
            op = {
                "voter": voter,
                "author": author,
                "permlink": permlink,
                "weight": int(weight)
            }
            ops.append(['vote', op])

        tx = self.finalizeOp(ops, wif)
        return tx

    def post(self, title, body, author, wif, **kwargs):
        """
        category = ''
        url = ''
        permlink = ''
        tags = []

        beneficiaries = 'login:10000'
        weight = 10000
        curation = max or int 2500..10000
        """

        asset = 'GBG'

        parent_beneficiaries = 'thallid'
        category = kwargs.pop("category", parent_beneficiaries)
        app = kwargs.pop("app", parent_beneficiaries)
        beneficiaries = kwargs.pop("beneficiaries", False)  # type: str

        if beneficiaries:
            a, w = beneficiaries.split(':')
            beneficiaries = [{"account": a, "weight": int(w)}]

        curation = kwargs.pop("curation", False)
        if curation == 'max':
            cur = self.get_curation_percent()
            if cur:
                curation = cur["max"]
            else:
                return False
        else:
            try:
                curation = int(curation)
            except:
                curation = False

        url = kwargs.pop("url", None)
        if url:
            parent_author, parent_permlink = self.resolve_url(url)  # comment
        else:
            parent_author, parent_permlink = '', category  # post

        permlink = kwargs.pop("permlink", None)
        if not permlink:
            # подготовить пермлинк самостоятельно
            permlink = ''.join([self.rus_d.get(s, s) for s in title.lower()]) + '-' + str(round(time()))

        tags = kwargs.pop("tags", ['test'])
        json_metadata = {"app": app, "tags": tags}

        max_accepted_payout = kwargs.pop("max_accepted_payout", 10000)
        allow_votes = kwargs.pop("allow_votes", True)
        allow_curation_rewards = kwargs.pop("allow_curation_rewards", True)

        ops = []
        op = {
            "parent_author": parent_author,
            "parent_permlink": parent_permlink,
            "author": author,
            "permlink": permlink,
            "title": title,
            "body": body,
            "json_metadata": json.dumps(json_metadata),
        }
        ops.append(['comment', op])

        extensions = []
        if beneficiaries:
            extensions.append([0, {"beneficiaries": beneficiaries}])
        if curation:
            extensions.append([2, {"percent": curation}])

        op = {
            "author": author,
            "permlink": permlink,
            "max_accepted_payout": '{:.{precision}f} {asset}'.format(
                float(max_accepted_payout),
                precision=self.asset_precision[asset],
                asset=asset
            ),
            "percent_steem_dollars": 10000,
            "allow_votes": allow_votes,
            "allow_curation_rewards": allow_curation_rewards,
            "extensions": extensions
        }
        ops.append(['comment_options', op])

        tx = self.finalizeOp(ops, wif)
        return tx

    def replace(self, title, body, author, wif, **kwargs):

        parent_beneficiaries = 'thallid'
        category = kwargs.pop("category", parent_beneficiaries)

        url = kwargs.pop("url", None)
        if url:
            parent_author, parent_permlink = self.resolve_url(url)  # comment
        else:
            parent_author, parent_permlink = '', category  # post

        permlink = kwargs.pop("permlink", None)
        if not permlink:
            log.debug('not permlink')
            return False

        app = kwargs.pop("app", parent_beneficiaries)
        tags = kwargs.pop("tags", ['golos'])
        json_metadata = {"app": app, "tags": tags}

        ops = []
        op = {
            "parent_author": parent_author,
            "parent_permlink": parent_permlink,
            "author": author,
            "permlink": permlink,
            "title": title,
            "body": body,
            "json_metadata": json.dumps(json_metadata),
        }
        ops.append(['comment', op])
        tx = self.finalizeOp(ops, wif)
        return tx

    def _transfer_op(self, to: str, amount: Number, from_account: str, asset: str = DEFAULT_ASSET, **kwargs) -> dict:
        """
        Generate a transfer operation as a ``dict`` based on the parameters.

        Note: If ``memo`` is not present in the ``**kwargs``, it will be excluded from the operation dict
              (this is intentional, to allow for operations such as vesting which do not use memos).

        :param str to: The username of the account to send coins to
        :param Decimal amount: The amount of coins to send, as either a ``Decimal``, ``str``, ``int`` or ``float``
        :param str from_account: The username of the account to send from
        :param str asset: The asset (coin) to send (Default: ``GOLOS`` (value of ``DEFAULT_ASSET``))
        :param str memo: An optional public message to attach to the transfer (Not included in op if not specified)

        :return dict op: An operation as a dict: ``dict(from:str, to:str, amount:str, memo:str?)``
        """
        op = {
            "from": from_account,
            "to": to,
            "amount": '{:.{precision}f} {asset}'.format(
                Decimal(amount), precision=self.asset_precision[asset], asset=asset
            )
        }
        if 'memo' in kwargs:
            op['memo'] = kwargs['memo']
        return op

    def transfer(self, to: str, amount: Number, from_account: str, wif: str, asset=DEFAULT_ASSET, memo='', **kwargs):
        """
        Transfer ``amount`` coins (of ``asset``) to ``from_account`` using the private key ``wif`` and the memo ``memo``

        **Basic usage:**

            >>> g = Api()
            >>> tf = golos.transfer(
            ...     to='ksantoprotein', amount='0.1', asset='GOLOS', from_account='someguy123',
            ...     wif='5Jq19TeeVmGrBFnu32oxfxQMiipnSCKmwW7fZGUVLAoqsKJ9JwP', memo='this is an example transfer'
            ... )
            >>> print('TXID:', tf['id'], 'Block:', tf['block_num'])
            TXID: c901c52daf57b60242d9d7be67f790e023cf2780 Block: 30895436


        :param str to: The username of the account you want to send coins to
        :param Decimal amount: The amount of coins to send, as either a ``Decimal``, ``str``, ``int`` or ``float``
        :param str from_account: The username of the account to send from
        :param str wif: The active/owner private key for the ``from_account``, as a string in WIF format
        :param str asset: The asset (coin) to send (Default: ``GOLOS`` (value of ``DEFAULT_ASSET``))
        :param str memo: An optional public message to attach to the transfer (Default: ``''`` - empty string)
        :param kwargs: Any additional keyword arguments
        :return dict transfer: A dictionary containing info about the completed transfer, inc. ``id`` (full ret below)

        **Return data**::

            dict(
                ref_block_num: int, ref_block_prefix:int,
                expiration:str, operations:list, extensions:list,
                signatures:List[str], block_num:int, id:str
            )


        """
        # to, amount, asset, from_account, [memo]

        ops = []
        op = self._transfer_op(to=to, amount=amount, asset=asset, from_account=from_account, memo=memo)
        ops.append(['transfer', op])
        tx = self.finalizeOp(ops, wif)
        return tx

    def transfers(self, raw_ops: List[Tuple[str, Number, str, str]], from_account: str, wif: str):
        """
        Execute multiple transfers in a single transaction.

            >>> tfrs = [('john', '1.234', 'GOLOS', 'thanks man'), ('dave', '0.374', 'GBG', 'hi dave'), ]
            >>> g = Api()
            >>> tf = g.transfers(raw_ops=tfrs, from_account='someguy123',
            ...                  wif='5Jq19TeeVmGrBFnu32oxfxQMiipnSCKmwW7fZGUVLAoqsKJ9JwP')
            >>> print('TXID:', tf['id'], 'Block:', tf['block_num'])
            TXID: c901c52daf57b60242d9d7be67f790e023cf2780 Block: 30895436


        :param List[Tuple] raw_ops: A list of transfers as 4 key tuples: ``(to:str, amount:str, asset:str, memo:str)``
        :param str from_account: The username of the account to send from
        :param str wif: The active/owner private key for the ``from_account``, as a string in WIF format

        :return dict transfer: A dictionary containing info about the completed TX, inc. ``id`` (full ret below)

        **Return data**::

            dict(
                ref_block_num: int, ref_block_prefix:int,
                expiration:str, operations:list, extensions:list,
                signatures:List[str], block_num:int, id:str
            )

        """
        ops = []
        for raw in raw_ops:
            to, amount, asset, memo = raw
            op = self._transfer_op(to=to, amount=amount, asset=asset, from_account=from_account, memo=memo)
            ops.append(['transfer', op])

        tx = self.finalizeOp(ops, wif)
        return tx

    def transfer_to_vesting(self, to: str, amount: Number, from_account: str, wif: str, **kwargs):
        """
        Power up a given amount of ``DEFAULT_ASSET`` (default: ``GOLOS``) from ``from_account`` into ``to``.


        **Basic Usage** (Convert 1000 GOLOS from ``someguy123`` into GESTS to ``someguy123``)

            >>> g = Api()
            >>> tf = g.transfer_to_vesting(
            ...   to='someguy123', from_account='someguy123', wif='5Jq19TeeVmGrBFnu32oxfxQMiipnSCKmwW7fZGUVLAoqsKJ9JwP'
            ...   amount='1000'
            ... )
            >>> print('TXID:', tf['id'], 'Block:', tf['block_num'])
            TXID: c901c52daf57b60242d9d7be67f790e023cf2780 Block: 30895436

        :param str to: The username of the account you want to send coins to
        :param Decimal amount: The amount of coins to send, as either a ``Decimal``, ``str``, ``int`` or ``float``
        :param str from_account: The username of the account to send from
        :param str wif: The active/owner private key for the ``from_account``, as a string in WIF format

        :return dict transfer: A dictionary containing info about the completed TX, inc. ``id`` (full ret below)

        **Return data**::

            dict(
                ref_block_num: int, ref_block_prefix:int,
                expiration:str, operations:list, extensions:list,
                signatures:List[str], block_num:int, id:str
            )

        """
        # to, amount, from_account
        ops = [[
            'transfer_to_vesting',
            self._transfer_op(to=to, amount=amount, asset=DEFAULT_ASSET, from_account=from_account)
        ], ]
        tx = self.finalizeOp(ops, wif)
        return tx

    def withdraw_vesting(self, account, amount, wif, **kwargs):
        # amount, account
        # понижается не менее 10х fee (сейчас 10 GOLOS которые нужно перевести в GEST)
        vesting_shares = self.convert_golos_to_vests(amount)
        asset = 'GESTS'

        ops = []
        op = {
            "account": account,
            "vesting_shares": '{:.{precision}f} {asset}'.format(
                vesting_shares,
                precision=self.asset_precision[asset],
                asset=asset
            ),
        }
        ops.append(['withdraw_vesting', op])
        tx = self.finalizeOp(ops, wif)
        return tx

    def account_create(self, login, password, creator, wif, **kwargs):
        create_with_delegation = False

        # login = account name must be at most 16 chars long, check if account already exists
        # roles = ["posting", "active", "memo", "owner"]
        paroles = self.key.get_keys(login, password)

        fee = self.account_creation_fee
        json_metadata = kwargs.pop("json_metadata", [])  ###

        owner_key_authority = [[paroles["public"]["owner"], 1]]
        active_key_authority = [[paroles["public"]["active"], 1]]
        posting_key_authority = [[paroles["public"]["posting"], 1]]
        memo = paroles["public"]["memo"]

        owner_accounts_authority = []
        active_accounts_authority = [[creator, 1]]
        posting_accounts_authority = [[creator, 1]]
        # active_accounts_authority = []
        # posting_accounts_authority = []

        ops = []
        op = {
            'fee': fee,
            'creator': creator,
            'new_account_name': login,
            'owner': {
                'weight_threshold': 1,
                'account_auths': owner_accounts_authority,
                'key_auths': owner_key_authority,
            },
            'active': {
                'weight_threshold': 1,
                'account_auths': active_accounts_authority,
                'key_auths': active_key_authority,
            },
            'posting': {
                'weight_threshold': 1,
                'account_auths': posting_accounts_authority,
                'key_auths': posting_key_authority,
            },
            'memo_key': memo,
            'json_metadata': json.dumps(json_metadata),
        }

        ops.append(['account_create', op])
        tx = self.finalizeOp(ops, wif)
        return tx

    def account_update_password(self, account, password, wif):

        paroles = self.key.get_keys(account, password)

        tx = self.get_accounts([account])[0]
        json_metadata = tx.get("json_metadata", {"profile": {}})

        log.debug(json_metadata)
        pprint(tx["owner"])
        pprint(tx["active"])
        pprint(tx["posting"])
        log.debug(tx["memo_key"])

        # public = self.key.get_public(wif)
        # print(public, tx["master_authority"]["key_auths"])

        # input('ready?')

        owner_key_authority = [[paroles["public"]["owner"], 1]]
        active_key_authority = [[paroles["public"]["active"], 1]]
        posting_key_authority = [[paroles["public"]["posting"], 1]]
        # owner_key_authority = False
        # active_key_authority = False
        # posting_key_authority = False

        memo = paroles["public"]["memo"]

        # Очистка авторити
        owner_accounts_authority = []
        active_accounts_authority = []
        posting_accounts_authority = []

        ops = []
        op = {
            "account": account,
            "owner": {
                'weight_threshold': 1,
                'account_auths': owner_accounts_authority,
                'key_auths': owner_key_authority,
            },
            "active": {
                'weight_threshold': 1,
                'account_auths': active_accounts_authority,
                'key_auths': active_key_authority,
            },
            "posting": {
                'weight_threshold': 1,
                'account_auths': posting_accounts_authority,
                'key_auths': posting_key_authority,
            },
            "memo_key": memo,
            # "json_metadata": json.dumps(json_metadata, ensure_ascii = False),
            "json_metadata": json_metadata,
        }
        ops.append(['account_update', op])

        tx = self.finalizeOp(ops, wif)
        return tx

    #####

    def change_recovery_account(self, account, recovery_account, wif):

        ops = []
        op = {
            "account_to_recover": account,
            "new_recovery_account": recovery_account,
            "extensions": [],
        }
        ops.append(['change_recovery_account', op])

        tx = self.finalizeOp(ops, wif)
        return tx

    def delegate_vesting_shares(self, delegatee, amount, delegator, wif, **kwargs):

        # делегируется не менее 0.010 GOLOS которые нужно перевести в GEST)
        vesting_shares = self.convert_golos_to_vests(amount)
        asset = 'GESTS'

        ops = []
        op = {
            "delegator": delegator,
            "delegatee": delegatee,
            "vesting_shares": '{:.{precision}f} {asset}'.format(
                vesting_shares,
                precision=self.asset_precision[asset],
                asset=asset
            ),
        }
        ops.append(['delegate_vesting_shares', op])
        tx = self.finalizeOp(ops, wif)
        return tx

    def account_create_with_delegation(self, login, password, creator, wif, **kwargs):

        # login = account name must be at most 16 chars long, check if account already exists
        # roles = ["posting", "active", "memo", "owner"]
        paroles = self.key.get_keys(login, password)

        fee = self.create_account_min_golos_fee
        # delegation = self.create_account_max_delegation
        vesting_shares = self.convert_golos_to_vests(10.0)  # aka 10 GOLOS delegation
        asset = 'GESTS'
        delegation = '{:.{precision}f} {asset}'.format(vesting_shares, precision=self.asset_precision[asset],
                                                       asset=asset)

        json_metadata = kwargs.pop("json_metadata", [])

        owner_key_authority = [[paroles["public"]["owner"], 1]]
        active_key_authority = [[paroles["public"]["active"], 1]]
        posting_key_authority = [[paroles["public"]["posting"], 1]]
        memo = paroles["public"]["memo"]

        owner_accounts_authority = []
        active_accounts_authority = []
        posting_accounts_authority = []
        # active_accounts_authority = [ [creator, 1] ]
        # posting_accounts_authority = [ [creator, 1] ]

        extensions = []

        ops = []
        op = {
            "fee": fee,
            "delegation": delegation,
            "creator": creator,
            "new_account_name": login,
            "owner": {
                "weight_threshold": 1,
                "account_auths": owner_accounts_authority,
                "key_auths": owner_key_authority,
            },
            "active": {
                "weight_threshold": 1,
                "account_auths": active_accounts_authority,
                "key_auths": active_key_authority,
            },
            "posting": {
                "weight_threshold": 1,
                "account_auths": posting_accounts_authority,
                "key_auths": posting_key_authority,
            },
            "memo_key": memo,
            "json_metadata": json.dumps(json_metadata),
            "extensions": extensions,
        }

        ops.append(['account_create_with_delegation', op])
        tx = self.finalizeOp(ops, wif)
        return tx

    def account_metadata(self, account, json_metadata, wif):

        ops = []
        op = {
            "account": account,
            "json_metadata": json.dumps(json_metadata, ensure_ascii=False)
        }
        ops.append(['account_metadata', op])

        tx = self.finalizeOp(ops, wif)
        return tx

    def delegate_vesting_shares_with_interest(self, delegatee, amount, delegator, rate, wif, **kwargs):

        # делегируется не менее 0.010 GOLOS которые нужно перевести в GEST)
        vesting_shares = self.convert_golos_to_vests(amount)
        asset = 'GESTS'

        ops = []
        op = {
            "delegator": delegator,
            "delegatee": delegatee,
            "vesting_shares": '{:.{precision}f} {asset}'.format(
                vesting_shares,
                precision=self.asset_precision[asset],
                asset=asset
            ),
            "interest_rate": rate,
            "extensions": [],
        }
        ops.append(['delegate_vesting_shares_with_interest', op])
        tx = self.finalizeOp(ops, wif)
        return tx

    #############################

    def follow(self, wtf, followings, followers, wif, **kwargs):

        # wtf = True (подписаться), False (отписаться), ignore - заблокировать
        # following - [] на кого подписывается
        # follower - [] кто подписывается

        if wtf and wtf != 'ignore':
            what = ['blog']  # подписаться
        elif wtf == 'ignore':
            what = ['ignore']  # заблокировать
        else:
            what = []  # отписаться

        ops = []
        for follower in followers:
            for following in followings:

                if follower != following:
                    json_body = [
                        'follow', {
                            "follower": follower,
                            "following": following,
                            "what": what
                        }
                    ]

                    f = {
                        "required_auths": [],
                        "required_posting_auths": [follower],
                        "id": 'follow',
                        "json": json.dumps(json_body)
                    }
                    ops.append(['custom_json', f])

        tx = self.finalizeOp(ops, wif)
        return tx

    def account_witness_proxy(self, account, proxy, wif):

        ops = []
        awp = {
            "account": account,
            "proxy": proxy,
        }
        ops.append(['account_witness_proxy', awp])
        tx = self.finalizeOp(ops, wif)
        return tx

    def repost(self, url, account, wif, **kwargs):

        # title = kwargs.pop("title", None)
        # body = kwargs.pop("body", None)
        # ['title', 'body', 'json_metadata']

        author, permlink = self.resolve_url(url)
        ops = []
        json_body = [
            'reblog', {
                "account": account,
                "author": author,
                "permlink": permlink
            }
        ]

        f = {
            "required_auths": [],
            "required_posting_auths": [account],
            "id": 'follow',
            "json": json.dumps(json_body)
        }
        ops.append(['custom_json', f])

        tx = self.finalizeOp(ops, wif)
        return tx

    #############################

    def get_curation_percent(self):
        tx = self.rpc.call('get_witness_schedule')
        try:
            min = int(tx["median_props"]["min_curation_percent"])
            max = int(tx["median_props"]["max_curation_percent"])
            return {"min": min, "max": max}
        except:
            return False

    def account_update(self, new_password, account, old_password, **kwargs):

        create_with_delegation = False

        # login = account name must be at most 16 chars long, check if account already exists
        # roles = ["posting", "active", "memo", "owner"]
        old_paroles = self.key.get_keys(account, old_password)
        new_paroles = self.key.get_keys(account, new_password)

        json_metadata = kwargs.pop("json_metadata", {})

        owner_key_authority = [[new_paroles["public"]["owner"], 1]]
        active_key_authority = [[new_paroles["public"]["active"], 1]]
        posting_key_authority = [[new_paroles["public"]["posting"], 1]]
        memo = new_paroles["public"]["memo"]

        owner_accounts_authority = []
        # active_accounts_authority = [ [creator, 1] ]
        # posting_accounts_authority = [ [creator, 1] ]
        active_accounts_authority = []
        posting_accounts_authority = []

        ops = []
        au = {
            'account': account,
            'owner': {
                'weight_threshold': 1,
                'account_auths': owner_accounts_authority,
                'key_auths': owner_key_authority,
            },
            'active': {
                'weight_threshold': 1,
                'account_auths': active_accounts_authority,
                'key_auths': active_key_authority,
            },
            'posting': {
                'weight_threshold': 1,
                'account_auths': posting_accounts_authority,
                'key_auths': posting_key_authority,
            },
            'memo_key': memo,
            'json_metadata': json.dumps(json_metadata),
        }

        ops.append(['account_update', au])
        tx = self.finalizeOp(ops, old_paroles["private"]["owner"])
        return tx

    def get_median_price(self):

        # Фид-прайс делегатов
        feed = self.rpc.call('get_feed_history')  # HF-18
        base = float(feed["current_median_history"]["base"].split()[0])
        quote = float(feed["current_median_history"]["quote"].split()[0])

        return round(base / quote, asset_precision["GBG"])

    @new_node_on_err(max_retries=MAX_RETRIES, delay=RETRY_DELAY)
    def get_follow(self, account: str):

        follow = {"follower": [], "following": []}
        account_follow = self.rpc.call('get_follow_count', account)

        # account_follow["follower_count"]
        # account_follow["following_count"]

        start_follower = 'a'
        while True:
            tx = self.rpc.call('get_followers', account, start_follower, 'blog', 1000)

            if len(tx) == 1 and tx[0]["follower"] == start_follower:
                follow["follower"].append(start_follower)
                break

            for line in tx[:-1]:
                follow["follower"].append(line["follower"])
            start_follower = tx[-1:][0]["follower"]

        start_follower = 'a'
        while True:
            tx = self.rpc.call('get_following', account, start_follower, 'blog', 100)

            if len(tx) == 1 and tx[0]["following"] == start_follower:
                follow["following"].append(start_follower)
                break

            for line in tx[:-1]:
                follow["following"].append(line["following"])
            start_follower = tx[-1:][0]["following"]

        account_follow["follower"] = follow["follower"]
        account_follow["following"] = follow["following"]

        return account_follow

    @retry_on_err(max_retries=MAX_RETRIES, delay=RETRY_DELAY)
    def get_account_reputations(self, account):

        # Определяем репутацию аккаунта
        reputations = self.rpc.call('get_account_reputations', [account])
        rep = int(reputations[0]["reputation"])
        if rep == 0:
            reputation = 25
        else:
            score = (math.log10(abs(rep)) - 9) * 9 + 25
            if rep < 0:
                score = 50 - score
            reputation = round(score, 3)

        return reputation

    def get_content(self, url, **kwargs):

        vote_limit = str(kwargs.pop("vote_limit", 0))

        author, permlink = self.resolve_url(url)
        user_post = self.rpc.call('get_content', author, permlink, vote_limit)

        return user_post

    # ----- account_by_key ----- #

    def get_key_references(self, public_key: str):
        """
        Позволяет узнать какому логину соответсвует публичный ключ
        #public_key = 'GLS6RGi692mJSNkdcVRunY3tGieJdTsa7AZeBVjB6jjqYg98ov5NL'
        Но не позволяет если есть авторити у аккаунта
        """

        res = self.rpc.call('get_key_references', [public_key])
        if res:
            return res[0]  # type: list
        else:
            # pprint(res)
            return False

    # ----- account_history ----- #

    # noinspection PyIncorrectDocstring
    @new_node_on_err(max_retries=MAX_RETRIES, delay=RETRY_DELAY)
    def get_account_history(self, account: str, op_limit: Union[list, str] = 'all', **kwargs) -> List[dict]:
        """
        Get the account history for a given ``account`` as a ``List[dict]``.
        
        Optionally you can filter the operations returned using ``op_limit``, as well as limit the number of operations
        with ``start_limit``, and maximum operation age with ``age``.
        
        **Basic usage**::
        
            >>> g = Api()
            >>> # Return a list of 'transfer' operations for the account 'someguy123'
            >>> hist = g.get_account_history('someguy123', op_limit='transfer')
            >>> h[0]
            {'from': 'someguy123', 'to': 'someguy123', 'amount': '0.100 GOLOS', 'memo': 'testing', 'number': 127290,
             'block': 30908474, 'timestamp': '2019-10-01T23:41:18', 'type_op': 'transfer',
             'trx_id': '80c7e0f7444f63074a52a8ba44cf066551706588'}
        
        :param str account: The username to load account history for, e.g. ``'someguy123'``
        :param list op_limit: Only return operations of these types. Specify either as a list: ``['transfer', 'vote']``,
                              or as a string, e.g. ``'transfer'`` (only transfers) or ``'all'`` (no filter)
        
        :param kwargs: See below

        :key int start_limit: Load at most this many history items (Default: ``1000`` items)
        :key int age: Skip history items older than this many seconds (Default: ``604800`` seconds / 7 days)
        
        :return List[dict] history: A ``list`` of ``dict`` history ops (see below for format)
        
        .. code-block:: python
            
            dict(from, to, amount: str, memo, number, block, timestamp: str, type_op, trx_id)
            
        
        """

        start_limit = kwargs.pop("start_limit", 1000)  # лимит одновременного запроса
        age_max = kwargs.pop("age", 7 * 24 * 60 * 60)  # время в сек до какой операции сканировать

        info = self.dynamic_global_properties
        raw = []

        start_block, flag, n = 999999999, True, 0
        while flag:
            history = self.rpc.call('get_account_history', account, start_block, start_limit)

            for h in reversed(history):
                number = h[0]
                block = h[1]["block"]
                timestamp = h[1]["timestamp"]
                type_op = h[1]["op"][0]

                op = h[1]["op"][1]
                op["number"] = number
                op["block"] = block
                op["timestamp"] = timestamp
                op["type_op"] = type_op
                op["trx_id"] = h[1]["trx_id"]

                if type_op in op_limit or op_limit == 'all':
                    raw.append(op)
                # pprint(op)
                # input('next')

                last_history_time = datetime.strptime(timestamp, time_format)
                age = (info["now"] - last_history_time).total_seconds() / 1
                if age > age_max:
                    flag = False
                    break

            start_block = h[0] - 1
            if start_block < start_limit:
                start_limit = start_block
            if start_limit <= 0:
                flag = False
            n += 1
            log.debug('%s %s %s', start_block, 'scan', n * start_limit)

        return raw

    # ----- database_api ----- #

    def get_account_count(self) -> int:
        # Возвращает количество зарегестрированных пользователей
        return int(self.rpc.call('get_account_count'))
    
    def vests_to_power(self, vests: Number) -> Decimal:
        """
        
        **Basic Usage**::
        
            >>> Api().vests_to_power('50058788')  # Convert ``50058788 GESTS`` into ``GOLOS``
            Decimal('15043.793')
        
        :param Number vests: An amount in VESTS/GESTS to convert to SP / GP
        :return Decimal power: The value of the VESTS / GESTS in STEEM / GOLOS
        """
        vests = Decimal(vests)
        info = self.dynamic_global_properties
        
        total_vests = Decimal(info['total_vesting_fund_steem'])
        total_shares = Decimal(info['total_vesting_shares'])
        return dec_round((total_vests * vests) / total_shares, dp=3, rounding=ROUND_DOWN)

    @new_node_on_err(max_retries=MAX_RETRIES, delay=RETRY_DELAY)
    def get_balances(self, *accounts) -> Dict[str, Dict[str, Decimal]]:
        """
        Get all balances for one or more ``accounts`` (as positional arguments).
        
        **Basic Usage**::
        
            >>> b = Api().get_balances('john', 'dave')
            >>> b['john']['GOLOS']
            Decimal('4183.323')
            >>> b['dave']['GBG']
            Decimal('837.978')
        
            
        :param str accounts: One or more usernames to get balances for
        :return dict balances: A dict of ``{account: {asset: balance, ..}, ..}``, for example:
        
        .. code-block:: python
        
            {
                'someguy123': {
                    'GOLOS': Decimal('157560.131'),
                    'GBG': Decimal('6420.916'),
                    'GP': Decimal('15044.951'),
                    'GESTS': Decimal('50058788.632180')
                }
            }
        
        
        """
        accs = self.get_accounts(list(accounts))
        res = {}
        for a in accs:
            b = res[a['name']] = {}
            for asset, akey in asset_account_keys.items():
                b[asset] = Decimal(a[akey])
        
        return res

    @new_node_on_err(max_retries=MAX_RETRIES, delay=RETRY_DELAY)
    def _get_accounts(self, logins: List[str], **kwargs) -> List[dict]:
        if type(logins) is str: logins = [logins]
        
        return self.rpc.call('get_accounts', logins)

    @new_node_on_err(max_retries=MAX_RETRIES, delay=RETRY_DELAY)
    def get_accounts(self, logins: List[str], **kwargs) -> List[dict]:
        """
        Перерасчитываются некоторые параметры по аккаунту
        "voting_power" - 1..10000 реальная батарейка
        "golos_power" - сила голоса с учетом делегирования
        "rshares" - сколько добавится шаров в пост при 100% батарейке
        "GOLOS", "GBG" - ликвидные токены
        "new_post_limit" - сколько постов можно опубликовать
        "new_post_time" - сколько осталось времени в минутах до публикации без штрафа
        "bandwidth" = {
            "avail" - всего доступно в кБ
            "used_forum" - использовано в кБ
            "used_market" - использовано в кБ
            "free_forum" - доступно в кБ
            "free_market" - доступно в кБ
            }
        "value" = {"GOLOS", "GBG"} - цена апвота по внутренней бирже
        "order" = {"GOLOS", "GBG"} - цена апвота по медиане
        "rating" = репутация в десятичном виде
        """
        if type(logins) is str: logins = [logins]

        add_follow = kwargs.pop("follow", False)

        accounts = self.rpc.call('get_accounts', logins)
        median_price = self.get_median_price()
        order_price = self.get_order_price()

        info = self.dynamic_global_properties
        if not info:
            log.debug('error in global data')
            raise GolosException('Error obtaining dynamic global props...')
        
        for account in accounts:

            # Определение реальной батарейки 1-10000

            VP = float(account["voting_power"])
            last_vote_time = datetime.strptime(account["last_vote_time"], time_format)
            age = (info["now"] - last_vote_time).total_seconds() / 1
            actualVP = VP + (10000 * age / 432000)

            if actualVP > 10000:
                account["voting_power"] = 10000
            else:
                account["voting_power"] = round(actualVP)

            # Определение golos_power (SP)

            vests = float(str(account["vesting_shares"]).split()[0])
            delegated = float(str(account["delegated_vesting_shares"]).split()[0])
            received = float(str(account["received_vesting_shares"]).split()[0])
            account["golos_power"] = round((vests + received - delegated) * info["golos_per_vests"],
                                           asset_precision["GOLOS"])

            # Определение rshares

            vesting_shares = int(1e6 * account["golos_power"] / info["golos_per_vests"])

            # max_vote_denom = info["vote_regeneration_per_day"] * (5 * 60 * 60 * 24) / (60 * 60 * 24)
            # used_power = int((account["voting_power"] + max_vote_denom - 1) / max_vote_denom)
            # rshares = ((vesting_shares * used_power) / 10000)
            # account["rshares"] = round(rshares)
            # account["add_reputation"] = round(rshares / 64)

            # Определение стоимости апвота

            # value_golos = round(account["rshares"] * info["total_reward_fund_steem"] / info["total_reward_shares2"],
            #                     asset_precision["GOLOS"])
            # value_gbg = round(value_golos * median_price, asset_precision["GBG"])
            # order_gbg = round(value_golos * order_price, asset_precision["GBG"])
            # account["value"] = {"GOLOS": value_golos, "GBG": value_gbg}
            # account["order"] = {"GOLOS": value_golos, "GBG": order_gbg}

            # Определение ликвидных токенов

            account["GOLOS"] = Decimal(str(account["balance"]).split()[0])
            account["GBG"] = Decimal(str(account["sbd_balance"]).split()[0])
            account["GESTS"] = Decimal(str(account["vesting_shares"]).split()[0])
            account["GP"] = self.vests_to_power(account['GESTS'])

            # Определение post_bandwidth

            account["new_post_time"] = 0  # minutes
            minutes_per_day = 24 * 60
            last_post_time = account.get("last_root_post")
            if last_post_time is not None:
                last_post_time = datetime.strptime(last_post_time, time_format)
                age_after_post = (info["now"] - last_post_time).total_seconds() / 60  # minutes
                if age_after_post >= minutes_per_day:
                    account["new_post_limit"] = 4
                else:
                    new_post_bandwidth = int(
                        (((minutes_per_day - age_after_post) / minutes_per_day) * account["post_bandwidth"]) + 10000)
    
                    if new_post_bandwidth > 40000:
                        account["new_post_limit"] = 0
                        account["new_post_time"] = round(
                            minutes_per_day - ((40000 - 10000) / (new_post_bandwidth - 10000)) * minutes_per_day)
                    else:
                        account["new_post_limit"] = int(4 - (new_post_bandwidth // 10000))

            # Определение update_account_bandwidth

            average_forum_bandwidth = int(account["average_bandwidth"])
            average_market_bandwidth = int(account["average_market_bandwidth"])

            info["max_virtual_bandwidth"] = int(info["max_virtual_bandwidth"]) / self.STEEMIT_BANDWIDTH_PRECISION

            average_seconds = 7 * 24 * 60 * 60

            last_forum_time = datetime.strptime(account["last_bandwidth_update"], time_format)
            last_market_time = datetime.strptime(account["last_market_bandwidth_update"], time_format)

            age_after_forum = int((info["now"] - last_forum_time).total_seconds() / 1)  # seconds
            age_after_market = int((info["now"] - last_market_time).total_seconds() / 1)  # seconds

            if age_after_forum >= average_seconds:
                new_account_forum_average_bandwidth = 0
            else:
                new_account_forum_average_bandwidth = ((
                                                               average_seconds - age_after_forum) * average_forum_bandwidth) / average_seconds

            if age_after_market >= average_seconds:
                new_account_market_average_bandwidth = 0
            else:
                new_account_market_average_bandwidth = ((
                                                                average_seconds - age_after_market) * average_market_bandwidth) / average_seconds

            avail = vesting_shares * info["max_virtual_bandwidth"]
            used_forum = new_account_forum_average_bandwidth * info["total_vesting_shares"]
            used_market = new_account_market_average_bandwidth * info["total_vesting_shares"]

            used_kb_forum = round(new_account_forum_average_bandwidth / self.STEEMIT_BANDWIDTH_PRECISION / 1024, 3)
            used_kb_market = round(new_account_market_average_bandwidth / self.STEEMIT_BANDWIDTH_PRECISION / 1024, 3)
            avail_kb = round(vesting_shares / info["total_vesting_shares"] * info[
                "max_virtual_bandwidth"] / self.STEEMIT_BANDWIDTH_PRECISION / 1024, 3)

            account["bandwidth"] = {
                "avail": avail_kb,
                "used_forum": used_kb_forum,
                "used_market": used_kb_market,
                "free_forum": round(avail_kb - used_kb_forum, 3),
                "free_market": round(avail_kb - used_kb_market, 3),
            }

            # Определение подписчиков

            # if add_follow:
            #   f = self.get_follow(account["name"])
            #   account["follower_count"] = f["follower_count"]
            #   account["following_count"] = f["following_count"]
            #   account["follower"] = f["follower"]
            #   account["following"] = f["following"]

            # Определение репутации
            # reputation, // <- Поле отсутствует, если выключен плагин follow

            rep = account.get("reputation", None)
            if not rep:
                rep = 0
            else:
                rep = int(rep)

            if rep == 0:
                account["rating"] = 25
            else:
                score = (math.log10(abs(rep)) - 9) * 9 + 25
                if rep < 0:
                    score = 50 - score
                account["rating"] = round(score, 3)

        return accounts

    @new_node_on_err(max_retries=MAX_RETRIES, delay=RETRY_DELAY)
    def get_block(self, n):
        return self.rpc.call('get_block', str(n))

    @new_node_on_err(max_retries=MAX_RETRIES, delay=RETRY_DELAY)
    def get_chain_properties(self) -> dict:
        """


        :return dict props: A dictionary of chain properties, containing:
        
        .. code-block:: python
        
                dict(account_creation_fee, maximum_block_size, sbd_interest_rate, create_account_min_golos_fee,
                     create_account_min_delegation, create_account_delegation_time, min_delegation,
                     max_referral_interest_rate, max_referral_term_sec, min_referral_break_fee, max_referral_break_fee,
                     posts_window, posts_per_window, comments_window, comments_per_window, votes_window,
                     votes_per_window, auction_window_size, max_delegated_vesting_interest_rate,
                     custom_ops_bandwidth_multiplier, min_curation_percent, max_curation_percent, curation_reward_curve,
                     allow_distribute_auction_reward, allow_return_auction_reward_to_fund)
        
          
        """
        return self.rpc.call('get_chain_properties')

    @new_node_on_err(max_retries=MAX_RETRIES, delay=RETRY_DELAY)
    def get_config(self):
        return self.rpc.call('get_config')

    @new_node_on_err(max_retries=MAX_RETRIES, delay=RETRY_DELAY)
    def get_database_info(self):
        return self.rpc.call('get_database_info')

    @new_node_on_err(max_retries=MAX_RETRIES, delay=RETRY_DELAY)
    def get_dynamic_global_properties(self) -> Union[bool, dict]:
        """
        
        :return dict dynamic_props: A dictionary containing the dynamic global properties (see below)
        
        .. code-block:: python
        
            dict(
                id, head_block_number, head_block_id, time, current_witness, total_pow, num_pow_witnesses,
                virtual_supply, current_supply, confidential_supply, current_sbd_supply, confidential_sbd_supply,
                sbd_interest_rate, sbd_print_rate, average_block_size, maximum_block_size, current_aslot,
                recent_slots_filled, participation_count, max_virtual_bandwidth, current_reserve_ratio,
                custom_ops_bandwidth_multiplier, is_forced_min_price, transit_block_num, transit_witnesses,
                total_vesting_fund_steem, total_reward_fund_steem, total_vesting_shares, total_reward_shares2,
                last_irreversible_block_num, vote_regeneration_per_day, golos_per_vests, now
            )
        
 
        """
        # Returns the global properties
        prop = self.rpc.call('get_dynamic_global_properties')

        # Obtain STEEM/VESTS ratio
        for p in ["total_vesting_fund_steem", "total_reward_fund_steem", "total_vesting_shares"]:
            value = prop.pop(p, None)
            prop[p] = float(value.split()[0])

        for p in ["total_reward_shares2", "last_irreversible_block_num", "vote_regeneration_per_day"]:
            value = prop.pop(p, None)
            if not value:
                log.debug("WARNING: %s not found in props. Skipping. Props were: %s", p, prop)
                continue
            prop[p] = int(value)

        prop["golos_per_vests"] = prop["total_vesting_fund_steem"] / prop["total_vesting_shares"]
        prop["now"] = datetime.strptime(prop["time"], time_format)

        return prop

    @new_node_on_err(max_retries=MAX_RETRIES, delay=RETRY_DELAY)
    def get_all_accounts(self):
        n = self.get_account_count()
        limit = 1000
        log.debug('find', n, 'accounts')

        accounts_dict = {}
        start_login = 'a'
        while True:
            log.debug(start_login)
            logins = self.rpc.call('lookup_accounts', start_login, limit)

            if len(logins) == 1 and logins[0] == start_login:
                accounts = self.get_accounts(logins)
                for account in accounts:
                    accounts_dict[account["name"]] = account
                break

            accounts = self.get_accounts(logins[:-1])
            for account in accounts:
                accounts_dict[account["name"]] = account

            start_login = logins[-1:][0]

        return accounts_dict

    ##### ##### follow ##### #####

    ##### ##### market_history ##### #####

    # def get_market_history(self):
    #   return self.rpc.call('get_market_history')

    def get_market_history_buckets(self):
        return self.rpc.call('get_market_history_buckets')

    def get_open_orders(self, account):
        return self.rpc.call('get_open_orders', account)

    def get_order_book(self, limit):
        return self.rpc.call('get_order_book', limit)

    def get_order_price(self):

        # усредненный прайс на внутренней бирже
        limit = 1
        feed = self.rpc.call('get_order_book', limit)
        ask = float(feed["asks"][0]["price"])
        bid = float(feed["bids"][0]["price"])

        return round((ask + bid) / 2, asset_precision["GBG"])

    def get_order_book_extended(self, limit):
        return self.rpc.call('get_order_book_extended', limit)

    def get_recent_trades(self, limit):
        return self.rpc.call('get_recent_trades', limit)

    def get_ticker(self):
        """
        try:
            t = {"bid": round(float(ticker["highest_bid"]), 6), "ask": round(float(ticker["lowest_ask"]), 6)}
        except:
            return False
        """
        return self.rpc.call('get_ticker')

    def get_tickers(self):
        ticker = self.rpc.call('get_ticker')
        try:
            bid = float(ticker["highest_bid"])
            ask = float(ticker["lowest_ask"])
            t = {"GOLOS_GBG": {"bid": bid, "ask": ask}, "GBG_GOLOS": {"bid": 1 / ask, "ask": 1 / bid}}
        except:
            return False

        return t

    def get_volume(self):
        return self.rpc.call('get_volume')

    ##### ##### network_broadcast_api ##### #####

    ##### ##### operation_history ##### #####

    def get_ops_in_block(self, n):
        return self.rpc.call('get_ops_in_block', str(n), True)

    ##### ##### social_network ##### #####

    ##### ##### tags ##### #####

    ##### ##### witness_api ##### #####

    def get_active_witnesses(self):
        return self.rpc.call('get_active_witnesses')

    def get_current_median_history_price(self):
        return self.rpc.call('get_current_median_history_price')

    def get_feed_history(self):
        return self.rpc.call('get_feed_history')

    def get_witness_by_account(self, account):
        return self.rpc.call('get_witness_by_account', account)

    def get_witness_count(self):
        return self.rpc.call('get_witness_count')

    def get_witness_schedule(self):
        return self.rpc.call('get_witness_schedule')

    # def get_witnesses(self, ids):
    #   return self.rpc.call('get_witnesses', ids)

    # def get_witnesses_by_vote(self, start, limit):
    #   return self.rpc.call('get_witnesses_by_vote', start, limit)

    def lookup_witness_accounts(self, start, limit):
        return self.rpc.call('lookup_witness_accounts', start, limit)

    ##### ##### differ ##### #####

    def resolve_url(self, url):

        if '#' in url:
            url = url.split('#')[1]
        if '@' in url:
            url = url.split('@')[1]

        if url[-1:] == '/':
            url = url[:-1]

        if url.count('/') != 1:
            return [False, False]
        else:
            return url.split('/')

    def convert_golos_to_vests(self, amount):

        info = self.get_dynamic_global_properties()
        if not info:
            log.debug('error in global data - convert_golos_to_vests')
            return False

        asset = 'GESTS'
        vests = round(float(amount) / info["golos_per_vests"], asset_precision[asset])

        return vests

    def check_login(self, login):

        if len(login) > 16:  # скорректировать под параметр блокчейна в инициализации
            return False
        if login[0] not in list('abcdefghijklmnopqrstuvwxyz'):
            return False
        for l in list(login[1:]):
            if l not in list('abcdefghijklmnopqrstuvwxyz0123456789.-'):
                return False

        return True

    def is_login(self, login):

        # Проверка существования логина
        account = self.rpc.call('get_accounts', [login])
        # account = self.get_accounts([login])
        if account:
            public_key = account[0]["posting"]["key_auths"][0][0]
            return public_key

        return False

    def __del__(self):
        self.rpc.close()


# ----- common def -----


def resolve_body_ru(body):
    raw_body = []
    body = body.replace('#', '')
    body = body.replace('\n', '#')
    for s in body:
        if s in rus_list:
            raw_body.append(s)
        elif s == '#':
            # raw_body.append('\n')
            raw_body.append('#')

    if len(raw_body) == 0:
        return False

    return ''.join(raw_body)
