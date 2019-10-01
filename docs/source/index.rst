.. _Privex Golos Python documentation:

Privex Golos Python documentation
=================================================

.. image:: https://www.privex.io/static/assets/svg/brand_text_nofont.svg
   :target: https://www.privex.io/
   :width: 400px
   :height: 400px
   :alt: Privex Logo
   :align: center


Welcome to the documentation for `Privex's Golos Python Library`_ - an open source Python 3 library designed
for interacting with the `GOLOS Classic`_ and potentially the `GOLOS`_ network.

This documentation is automatically kept up to date by ReadTheDocs, as it is automatically re-built each time
a new commit is pushed to the `Github Project`_

.. _Privex's Golos Python Library: https://github.com/Privex/golos-python
.. _Github Project: https://github.com/Privex/golos-python
.. _GOLOS Classic: https://github.com/golos-classic/golos
.. _GOLOS: https://github.com/GolosChain/golos

QuickStart
==========

To install ``golos-python`` - simply download it using ``pip``, just like any other package :)

.. code-block:: bash

    pip3 install golos-python

For alternative installation methods, see :ref:`Installation`

Below are some common examples for using the library:

.. code-block:: python

    from golos import Api

    # The ``nodes`` parameter is optional. By default it will use the node list specified in ``golos.storage.nodes``
    golos = Api(nodes=['wss://golosd.privex.io', 'wss://api.golos.blckchnd.com/ws'])

    ###
    # Get account information + balances
    ###

    accounts = golos.get_accounts(['someguy123'])
    acc = accounts[0]
    print(acc['owner'])
    # 'someguy123'

    print('GOLOS:', acc['GOLOS'], 'GBG:', acc['GBG'])
    # GOLOS: 157560.231 GBG: 6420.916

    ###
    # Get witness information
    ###

    witness = golos.get_witness_by_account(account='someguy123')
    print(witness['url'])
    # 'https://golos.io/ru--delegaty/@someguy123/delegat-someguy123'

    ###
    # Get account history
    ###

    history = golos.get_account_history(account='someguy123')

    print(history[0])
    # {'account': 'huso', 'witness': 'someguy123', 'approve': False, 'number': 127286, 'block': 30494335,
    #  'timestamp': '2019-09-17T14:20:21', 'type_op': 'account_witness_vote'}

    ###
    # Transfer GOLOS / GBG to another account
    #
    # WARNING: To reduce the risk of rounding errors, pass the amount as either a string or a Decimal() - avoid float's!
    ###

    tf = golos.transfer(
        to='ksantoprotein', amount='0.1', asset='GOLOS', from_account='someguy123',
        wif='5Jq19TeeVmGrBFnu32oxfxQMiipnSCKmwW7fZGUVLAoqsKJ9JwP', memo='this is an example transfer'
    )

    print('TXID:', tf['id'], 'Block:', tf['block_num'])
    # TXID: c901c52daf57b60242d9d7be67f790e023cf2780 Block: 30895436






Contents
=========

.. toctree::
   :maxdepth: 8
   :caption: Main:

   self
   install


.. toctree::
   :maxdepth: 8
   :caption: Code Documentation:

   code/index
   code/tests



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`