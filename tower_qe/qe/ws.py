from Queue import Queue, Empty
import threading
import logging
import atexit
import json
import ssl

import websocket
import requests

from qe.config import config


log = logging.getLogger(__name__)


class WSClient(object):

    def __init__(self, token, hostname='', port=8080, secure=True):
        self.port = port
        self._use_ssl = secure
        if not hostname:
            pref = 'https://' if secure else 'http://'
            hostname = config.base_url.split(pref)[1].split(':')[0]
        self.hostname = hostname
        self.token = token
        self.sid = self._get_session_id()
        self._recv_queue = Queue()
        self._signal_queue = Queue()
        self.ws = websocket.WebSocketApp('', on_message=self._on_message,
                                         on_error=self._on_error,
                                         on_close=self._on_close,
                                         on_ping=self._on_ping,
                                         on_pong=self._on_pong)
        self.kill_flag = threading.Event()
        self._message_cache = []

    def connect(self):
        pref = 'wss://' if self._use_ssl else 'ws://'
        url = '{0}{1.hostname}:{1.port}/socket.io/1/websocket/{1.sid}?Token={1.token}'.format(pref, self)
        self.ws.url = url
        self._ws_thread = threading.Thread(target=self._ws_run_forever, args=(self.ws, {"cert_reqs": ssl.CERT_NONE}))
        self._ws_thread.start()
        atexit.register(self.ws.close)

    def close(self):
        self.ws.close()

    def recv(self, wait=False, timeout=10):
        try:
            msg = self._recv_queue.get(wait, timeout)
        except Empty:
            return None
        content = msg.split('5::/socket.io/')[1]
        group, data = content.split(':', 1)
        data = json.loads(data)
        return group, data

    def send(self, data):
        self.ws.send(data)
        log.debug('successfully sent {}'.format(data))

    def subscribe(self, *groups):
        for group in groups:
            self.subscribe_to_group(group)

    def subscribe_to_group(self, group):
        rqst = "1::/socket.io/{0}".format(group)
        self.send(rqst)
        try:
            conf = self._signal_queue.get(True, 10)
        except Empty:
            raise(Exception("Never received confirmation from server."))
        if conf != rqst:
            raise(Exception("Failed to receive desired subscription confirmation: {}".format(conf)))
        return True

    def _get_session_id(self):
        pref = 'https://' if self._use_ssl else 'http://'
        url = '{0}{1.hostname}:{1.port}/socket.io/1/?Token={1.token}'.format(pref, self)
        r = requests.get(url, verify=False)
        return r.content.split(':')[0]

    def _on_message(self, ws, message):
        if message in ('1::',):
            log.debug('received sio init')
            return  # considered noise atm
        elif message == '2::':  # socket.io heartbeat
            log.debug('received sio hb')
            return self.ws.send('2::')
        elif message.startswith('1::/socket.io/'):
            log.debug('received signal: {}'.format(message))
            return self._signal_queue.put(message)
        else:
            log.debug('received message: {}'.format(message))
            return self._recv_queue.put(message)

    def _on_error(self, ws, error):
        log.info('Error received: {}'.format(error))

    def _on_close(self, ws):
        log.info('Successfully closed ws.')

    def _on_ping(self, ws, *args):  # not used by socket.io
        log.info('ON PING: {}'.format(args))

    def _on_pong(self, ws, *args):  # not used by socket.io
        log.info('ON PONG: {}'.format(args))

    def _ws_run_forever(self, ws, sslopt):
        ws.run_forever(sslopt=sslopt)
        log.info('ws.run_forever finished')

    def __iter__(self):
        while True:
            val = self.recv()
            if not val:
                return
            yield val
