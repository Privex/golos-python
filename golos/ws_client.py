# -*- coding: utf-8 -*-
"""
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
from typing import Union, List

import websocket
import ssl
import json
import logging
from golos import storage
from .storage import api_total
from time import sleep
from pprint import pprint
from itertools import cycle
from .exceptions import GolosException, APINotFound

log = logging.getLogger(__name__)


def _find_exception(msg):
    if 'could not find api' in msg.lower():
        raise APINotFound(msg)

    raise GolosException(msg)


def error_handler(data: dict = None, msg: str = None):
    if msg is not None or data is None:
        msg = 'Unknown Golos Error...' if msg is None else msg
        return _find_exception(msg=msg)

    err = data.get("error", {})
    msg, errdata = err.get("message", 'Unknown Golos Error...'), err.get("data", {})

    # Replace format variables such as ${api} with data['api']
    for k, d in errdata.items():
        fmtvar = '${' + k + '}'
        while fmtvar in msg:
            msg = msg.replace('${' + k + '}', f'"{d}"')

    msg = f"Error Code {err.get('code', 'n/a')}: {msg}"
    log.error('GOLOS Error: %s', msg)
    log.error('Raw error: %s', err)

    return _find_exception(msg=msg)


class WsClient:
    """ Simple Golos JSON-WebSocket-RPC API
        This class serves as an abstraction layer for easy use of the Golos API.

        rpc = WsClient(nodes = nodes) or rpc = WsClient()
        Args:
            nodes (list): A list of Golos WebSocket RPC nodes to connect to.

        any call available to that port can be issued using the instance
        rpc.call('command', *parameters)
    """
    nodes: List[str]
    report: bool
    api_total: dict
    url: str
    ws: websocket.WebSocket

    def __init__(self, report=False, nodes: Union[List[str], str] = None, **kwargs):
        self.report = report
        self.num_retries = kwargs.get("num_retries", 20)
        nodes = [nodes] if type(nodes) is str else nodes
        self.nodes = cycle(storage.nodes if nodes is None else nodes)  # Перебор нод
        self.api_total = api_total
        self.url = ''
        self.ws = None
        self.ws_connect()  # Подключение к ноде

    def ws_connect(self):
        cnt = 0
        while True:
            cnt += 1
            self.url = next(self.nodes)
            if self.report:
                log.info("Trying to connect to node %s", self.url)
            if self.url[:3] == "wss":
                sslopt_ca_certs = {'cert_reqs': ssl.CERT_NONE}
                self.ws = websocket.WebSocket(sslopt=sslopt_ca_certs)
            else:
                self.ws = websocket.WebSocket()

            try:
                self.ws.connect(self.url)
                break
            except KeyboardInterrupt:
                raise
            except:
                if 0 <= self.num_retries < cnt:
                    raise Exception

                sleeptime = (cnt - 1) * 2 if cnt < 10 else 10
                if sleeptime:
                    log.info("Lost connection to node during wsconnect(): %s (%d/%d) ", self.url, cnt, self.num_retries)
                    log.info("Retrying in %d seconds", sleeptime)
                    sleep(sleeptime)

    def call(self, name, *args):
        # Определяем для name своё api
        api = self.api_total[name]
        if api:
            body_dict = {"id": 1, "method": "call", "jsonrpc": "2.0", "params": [api, name, args]}
            body = json.dumps(body_dict, ensure_ascii=False).encode('utf8')
        else:
            if self.report:
                log.warning('not find api in api_total')
            return False

        response, result = None, []

        cnt = 0
        while True:
            cnt += 1

            try:
                self.ws.send(body)
                response = self.ws.recv()
                # pprint(response)
                break
            except KeyboardInterrupt:
                raise
            except:
                if -1 < self.num_retries < cnt:
                    raise Exception  # возможно сделать return False
                sleeptime = (cnt - 1) * 2 if cnt < 10 else 10
                if sleeptime:
                    log.info("Lost connection to node during call(): %s (%d/%d) ", self.url, cnt, self.num_retries)
                    log.info("Retrying in %d seconds", sleeptime)
                    sleep(sleeptime)

                # retry
                try:
                    self.ws.close()
                    sleep(sleeptime)
                    self.ws_connect()
                except:
                    pass

        if not response:
            if self.report:
                log.error('not response')
            return False
        rj = response_json = json.loads(response)  # Нет проверки на ошибки при загрузке данных

        if 'error' in response_json:
            return error_handler(rj)
        if 'result' not in response_json:
            if self.report:
                log.error("No 'result' key found in response...")
            return False

        return response_json.get("result")

    def close(self):
        if self.ws is not None:
            self.ws.close()

    # def __exit__(self, exc_type, exc_val, exc_tb):
    #     self.close()

    def __del__(self):
        self.close()


# ----- main -----
if __name__ == '__main__':
    log.debug('connect')
    rpc = WsClient()
    log.debug('try call')

    i = rpc.call('get_dynamic_global_properties')
    # i = rpc.call('get_accounts', ['koss'])
    # i = rpc.call('get_block', '20005000')
    pprint(i)

    log.debug('yet')
