from Queue import Queue, Empty
import threading
import logging
import atexit
import json
import ssl

import websocket

from qe.config import config


log = logging.getLogger(__name__)


class WSClient(object):
    """Provides a basic means of testing pub/sub notifications with payloads similar to
       {'groups': {'jobs': ['status_changed', 'summary'],
                   'schedules': ['changed'],
                   'ad_hoc_command_events': [ids,],
                   'job_events': [ids,],
                   'control': ['limit_reached']}}

    e.x:
    ```
    ws = WSClient(token, port=8013, secure=False).connect()
    ws.job_details()
    ... # launch job
    job_messages = [msg for msg in ws]
    ws.ad_hoc_stdout()
    ... # launch ad hoc command
    ad_hoc_messages = [msg for msg in ws]
    ws.close()
    ```
    """
    # Subscription group types
    changed = 'changed'
    limit_reached = 'limit_reached'
    status_changed = 'status_changed'
    summary = 'summary'

    def __init__(self, token, hostname='', port=8080, secure=True):
        self.port = port
        self._use_ssl = secure
        if not hostname:
            pref = 'https://' if secure else 'http://'
            hostname = config.base_url.split(pref)[1].split(':')[0]
        self.hostname = hostname
        self.token = token
        self._recv_queue = Queue()
        self.ws = websocket.WebSocketApp('', on_message=self._on_message,
                                         on_error=self._on_error,
                                         on_close=self._on_close)
        self._message_cache = []
        self._should_subscribe_to_pending_job = False

    def connect(self):
        pref = 'wss://' if self._use_ssl else 'ws://'
        url = '{0}{1.hostname}:{1.port}/websocket/'.format(pref, self)
        self.ws.url = url
        self._ws_thread = threading.Thread(target=self._ws_run_forever, args=(self.ws, {"cert_reqs": ssl.CERT_NONE}))
        self._ws_thread.start()
        atexit.register(self.ws.close)
        return self

    def close(self):
        self.ws.close()

    # mirror page behavior
    def job_details(self):
        self._should_subscribe_to_pending_job = dict(jobs=[self.status_changed, self.summary],
                                                     events='job_events')
        self.subscribe(jobs=[self.status_changed, self.summary])

    # mirror page behavior
    def job_stdout(self):
        self._should_subscribe_to_pending_job = dict(jobs=[self.status_changed],
                                                     events='job_events')
        self.subscribe(jobs=[self.status_changed])

    # mirror page behavior
    def ad_hoc_stdout(self):
        self._should_subscribe_to_pending_job = dict(jobs=[self.status_changed],
                                                     events='ad_hoc_command_events')
        self.subscribe(jobs=[self.status_changed])

    # mirror page behavior
    def jobs_list(self):
        self.subscribe(jobs=[self.status_changed, self.summary], schedules=[self.changed])

    # mirror page behavior
    def dashboard(self):
        self.subscribe(jobs=[self.status_changed])

    def subscribe(self, **groups):
        """ws.subscribe(jobs=[ws.status_changed, ws.summary],
                        job_events=[1,2,3])"""
        self._subscribe(groups=groups)

    def _subscribe(self, **payload):
        self._send(json.dumps(payload))

    def unsubscribe(self):
        self._send(json.dumps(dict(groups={})))

    def _on_message(self, ws, message):
        message = json.loads(message)
        log.debug('received message: {}'.format(message))
        {"status": "pending", "unified_job_id": 9, "group_name": "jobs"}

        if all([message.get('group_name', None) == 'jobs',
                message.get('status', None) == 'pending',
                message.get('unified_job_id', None),
                not message.get('project_id', False),
                self._should_subscribe_to_pending_job]):
            self._update_subscription(message['unified_job_id'])

        return self._recv_queue.put(message)

    def _update_subscription(self, job_id):
        subscription = dict(jobs=self._should_subscribe_to_pending_job['jobs'])
        events = self._should_subscribe_to_pending_job['events']
        subscription[events] = [job_id]
        self.subscribe(**subscription)
        self._should_subscribe_to_pending_job = False

    def _on_error(self, ws, error):
        log.info('Error received: {}'.format(error))

    def _on_close(self, ws):
        log.info('Successfully closed ws.')

    def _ws_run_forever(self, ws, sslopt):
        ws.run_forever(sslopt=sslopt)
        log.info('ws.run_forever finished')

    def _recv(self, wait=False, timeout=10):
        try:
            msg = self._recv_queue.get(wait, timeout)
        except Empty:
            return None
        return msg

    def _send(self, data):
        self.ws.send(data)
        log.debug('successfully sent {}'.format(data))

    def __iter__(self):
        while True:
            val = self._recv()
            if not val:
                return
            yield val
