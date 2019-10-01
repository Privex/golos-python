# -*- coding: utf-8 -*-

import websocket
import ssl
import json
import logging
from golos import storage
from .storage import api_total
from time import sleep
from pprint import pprint
from itertools import cycle

log = logging.getLogger(__name__)


class WsClient:
    """ Simple Golos JSON-WebSocket-RPC API
        This class serves as an abstraction layer for easy use of the Golos API.

        rpc = WsClient(nodes = nodes) or rpc = WsClient()
        Args:
            nodes (list): A list of Golos WebSocket RPC nodes to connect to.

        any call available to that port can be issued using the instance
        rpc.call('command', *parameters)
    """

    def __init__(self, report=False, nodes=None, **kwargs):
        self.report = report
        self.num_retries = kwargs.get("num_retries", 20)
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
                log.info("Trying to connect to node %s" % self.url)
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
        response_json = json.loads(response)  # Нет проверки на ошибки при загрузке данных

        if 'error' in response_json:
            if self.report:
                log.error('find error')
                log.error(response_json["error"]["message"])
            return False
        if 'result' not in response_json:
            if self.report:
                log.error('not result')
            return False

        return response_json.get("result")


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
