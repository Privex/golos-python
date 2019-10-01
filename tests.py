#!/usr/bin/env python3
"""
Privex Golos-Python Unit Tests

**To run these tests**:

.. code-block:: bash

    pip3 install -r requirements.txt
    pytest -v tests.py


**Enabling extra logging output**:

If you want to see the logging output of the library, use the ``DEBUG`` environment variable, and execute ``tests.py``
directly (not via pytest, as pytest will filter out the log messages):


.. code-block:: bash

    DEBUG=true ./tests.py -vv


**Copyright**::

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
import unittest
import logging
from golos import Api, storage, Key
from privex.loghelper import LogHelper
from privex.helpers import env_bool

NODES = ['wss://golosd.privex.io'] + storage.nodes
TEST_ACCOUNTS = ['someguy123', 'ksantoprotein']
TEST_WITNESSES = ['someguy123']

DEBUG = env_bool('DEBUG', False)

lh = LogHelper('golos', handler_level=logging.DEBUG if DEBUG else logging.WARNING)
lh.add_console_handler()
log = lh.get_logger()


class GolosTestCase(unittest.TestCase):
    def setUp(self):
        self.golos = Api(nodes=NODES, report=DEBUG)

    def test_get_account(self):
        """Testing Api.get_accounts returns valid account dictionaries"""
        a = self.golos.get_accounts(TEST_ACCOUNTS)
        self.assertIs(type(a), list)
        self.assertEqual(len(a), len(TEST_ACCOUNTS))
        for i, acc in enumerate(a):
            # log.info('get_accounts %s = %s', acc, a)
            self.assertIs(type(acc), dict, msg=f'type(acc) is dict')
            self.assertIn('name', acc, msg=f"'name' in acc")
            self.assertEqual(acc['name'], TEST_ACCOUNTS[i], msg=f'{acc["name"]} == {TEST_ACCOUNTS[i]}')
            self.assertIs(type(acc['owner']), dict, msg="type(acc['owner']) is dict")
            self.assertIs(type(acc['mined']), bool, msg="type(acc['mined']) is bool")
            self.assertIs(type(acc['witness_votes']), list, msg="type(acc['witness_votes']) is list")

    def test_get_account_history(self):
        """Testing Api.get_account_history returns a non-empty list containing valid history items"""
        for a in TEST_ACCOUNTS:
            h = self.golos.get_account_history(account=a)
            self.assertIs(type(h), list)
            self.assertGreater(len(h), 0)
            for x in h:
                self.assertIs(type(x), dict)
                self.assertIn('type_op', x)

    def test_get_witness(self):
        """Testing Api.get_witness returns a valid witness info dictionary"""
        for a in TEST_WITNESSES:
            w = self.golos.get_witness_by_account(a)
            self.assertIs(type(w), dict)
            self.assertEqual(w['owner'], a)
            self.assertIs(type(w['props']), dict)
            self.assertIs(type(w['total_missed']), int)


class GolosKeyTests(unittest.TestCase):
    
    def test_compare_keys(self):
        """Test that Key.is_key correctly verifies a public key matches a private key"""
        
        kp1 = '5Jq19TeeVmGrBFnu32oxfxQMiipnSCKmwW7fZGUVLAoqsKJ9JwP', \
              'GLS7qHue1h2eWV8M7WKtb6F8dbhKfEFvLVy9JqvSTHBBEM5JMdsmh'
        
        kp2 = '5KPQo2iNeACYagW5qAsgNpFxDDuwuArCCG8PvU6FKTMcD5LmhzJ', \
              'GLS8G7rgqhPUbyzYVYWb8BPcHtpgLDmJYooHmHPbaLaH7cdywsdwm'
        
        t1 = Key.is_key(kp1[0], kp1[1])  # Compare keypair 1's private key against it's own public key
        t2 = Key.is_key(kp1[0], kp2[1])  # Compare keypair 1's private key against keypair 2's public key
        self.assertTrue(t1)
        self.assertFalse(t2)
    
    def test_get_public(self):
        """Test Key.get_public_from_private returns the correct public key"""
        pub = Key.get_public_from_private('5Jq19TeeVmGrBFnu32oxfxQMiipnSCKmwW7fZGUVLAoqsKJ9JwP')
        self.assertEqual(pub, 'GLS7qHue1h2eWV8M7WKtb6F8dbhKfEFvLVy9JqvSTHBBEM5JMdsmh')
    
    def test_account_keys(self):
        """Test Key.get_keys correctly generates account public/private keys"""
        acc = Key.get_keys('someguy123', 'example')
        
        for r in Key.roles:
            self.assertIn(r, acc['private'], msg=f'{r} in acc["private"]')
            self.assertIn(r, acc['public'], msg=f'{r} in acc["public"]')
        
        self.assertEqual(acc['private']['active'], '5KME2a7DBdGBdpAwLC4tGmJ8mSz9HgZkcMtKc8rkADn6cLZyvPc')
        self.assertEqual(acc['public']['active'], 'GLS7LjcmXF4mf9z3MNgcceSvMG8oezEtGhcL4yAXpJWFZxdX47ET7')
        

if __name__ == "__main__":
    unittest.main()
