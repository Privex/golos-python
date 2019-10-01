# Privex's GOLOS Python Library

[![Documentation Status](https://readthedocs.org/projects/golos-python/badge/?version=latest)](https://golos-python.readthedocs.io/en/latest/?badge=latest) 
[![Build Status](https://travis-ci.com/Privex/golos-python.svg?branch=master)](https://travis-ci.com/Privex/golos-python) 
[![Codecov](https://img.shields.io/codecov/c/github/Privex/golos-python)](https://codecov.io/gh/Privex/golos-python)  
[![PyPi Version](https://img.shields.io/pypi/v/golos-python.svg)](https://pypi.org/project/golos-python/)
![License Button](https://img.shields.io/pypi/l/golos-python) 
![PyPI - Downloads](https://img.shields.io/pypi/dm/golos-python)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/golos-python) 
![GitHub last commit](https://img.shields.io/github/last-commit/Privex/golos-python)

This is a Python 3 library designed for GOLOS Classic (may work with other GOLOS forks) developed and published by
[Privex Inc.](https://www.privex.io/)

A large portion of the code was originally sourced from [@ksantoprotein](https://golos.io/@ksantoprotein), while we've
cleaned it up, made some improvements, added unit tests, and packaged it into a PyPi package.

```
    +===================================================+
    |                 © 2019 Privex Inc.                |
    |               https://www.privex.io               |
    +===================================================+
    |                                                   |
    |        Originally Developed by Privex Inc.        |
    |                                                   |
    |        Core Developer(s):                         |
    |                                                   |
    |          (+)  Chris (@someguy123) [Privex]        |
    |                                                   |
    +===================================================+
```

# Install

### Download and install from PyPi using pip (recommended)

```sh
pip3 install golos-python
```

### (Alternative) Manual install from Git

**Option 1 - Use pip to install straight from Github**

```sh
pip3 install git+https://github.com/Privex/golos-python
```

**Option 2 - Clone and install manually**

```bash
# Clone the repository from Github
git clone https://github.com/Privex/golos-python
cd golos-python

# RECOMMENDED MANUAL INSTALL METHOD
# Use pip to install the source code
pip3 install .

# ALTERNATIVE MANUAL INSTALL METHOD
# If you don't have pip, or have issues with installing using it, then you can use setuptools instead.
python3 setup.py install
```


# License

This Python module was created by [Privex Inc. of Belize City](https://www.privex.io), and licensed under the X11/MIT License.
See the file [LICENSE](https://github.com/Privex/golos-python/blob/master/LICENSE) for the license text.

**TL;DR; license:**

We offer no warranty. You can copy it, modify it, use it in projects with a different license, and even in commercial (paid for) software.

The most important rule is - you **MUST** keep the original license text visible (see `LICENSE`) in any copies.

# Example uses

```python

from golos import Api
from decimal import Decimal

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

```
# Contributing

We're happy to accept pull requests, no matter how small.

Please make sure any changes you make meet these basic requirements:

 - Any code taken from other projects should be compatible with the MIT License
 - This is a new project, and as such, supporting Python versions prior to 3.4 is very low priority.
 - However, we're happy to accept PRs to improve compatibility with older versions of Python, as long as it doesn't:
   - drastically increase the complexity of the code
   - OR cause problems for those on newer versions of Python.

**Legal Disclaimer for Contributions**

Nobody wants to read a long document filled with legal text, so we've summed up the important parts here.

If you contribute content that you've created/own to projects that are created/owned by Privex, such as code or 
documentation, then you might automatically grant us unrestricted usage of your content, regardless of the open source 
license that applies to our project.

If you don't want to grant us unlimited usage of your content, you should make sure to place your content
in a separate file, making sure that the license of your content is clearly displayed at the start of the file 
(e.g. code comments), or inside of it's containing folder (e.g. a file named LICENSE). 

You should let us know in your pull request or issue that you've included files which are licensed
separately, so that we can make sure there's no license conflicts that might stop us being able
to accept your contribution.

If you'd rather read the whole legal text, it should be included as `privex_contribution_agreement.txt`.


# Thanks for reading!

**If this project has helped you, consider [grabbing a VPS or Dedicated Server from Privex](https://www.privex.io) -** 
**prices start at as little as US$8/mo (we take cryptocurrency!)**
