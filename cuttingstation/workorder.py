from multiprocessing import Process
from HTMLParser import HTMLParser
from config import Config
from time import sleep
import requests
import requests.exceptions
import json
import logging
import itertools


class WebClient(Process):
    def __init__(self):
        Process.__init__(self)
        self.log = logging.getLogger(__name__)
        self.config = None
        self.client = None
        self.authenticated = False
        self.last_wo_id = None
        self.station = None

    def run(self):
        try:
            self.config = Config()
            self.client = requests.Session()
            self.login()
            while True:
                wo_id = self.get_station().get('active_work_order', None)
                if wo_id != self.last_wo_id:
                    work_order = WorkOrder(self.get_active_work_order())
                    self.log.debug("Loaded work order #%s" % work_order.number)

                self.last_wo_id = wo_id
                sleep(3)
        except KeyboardInterrupt:
            return

    def login(self):
        try:
            # Get the login page
            response = self.client.get(self.config.url + '/login', timeout=1)

            # Get form xsrf token
            xsrf = XSRF()
            xsrf.feed(response.text)

            # Send login data
            self.client.post(self.config.url + '/login',
                             data={'_xsrf': xsrf.value,
                                   'username': self.config.username,
                                   'password': self.config.password},
                             timeout=1)

            # Check if authentication was successful
            if 'uid' in self.client.cookies:
                self.station = json.loads(self.client.get(self.config.url + '/api/v1/station/').text)['id']
                self.authenticated = True
            else:
                self.log.warning("Login failed")
                self.authenticated = False
        except (requests.exceptions.RequestException, KeyError):
            self.authenticated = False

    def get_station(self):
        return self.get_json('/api/v1/station/')

    def get_active_work_order(self):
        return self.get_json('/api/v1/station/%s/active_work_order' % self.station)

    def get(self, url, **kwargs):
        # Make sure we're authenticated before making requests
        while not self.authenticated:
            self.login()
            sleep(3)  # Rate limit login attemps

        # Append url from config to url
        url = self.config.url + '/' + url.lstrip('/')

        # Use a default timeout of 1 second
        if 'timeout' not in kwargs:
            kwargs['timeout'] = 1

        try:
            r = self.client.get(url, **kwargs)
            if r.status_code == 401:
                self.log.warning("Access denied: %s" % url)
        except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout):
            self.authenticated = False
            self.station = None
            self.client = requests.Session()
            self.log.warning("Connection error")
            while not self.authenticated:
                self.log.debug("Connection error, retrying login")
                self.login()
                sleep(3)  # Rate limit login attempts
            r = self.client.get(url, **kwargs)
        return r

    def get_json(self, url, **kwargs):
        r = self.get(url, **kwargs)
        try:
            result = json.loads(r.text)
        except (ValueError, TypeError) as e:
            result = {}
        return result


class XSRF(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.value = None

    def handle_starttag(self, tag, attrs):
        xsrf = dict(attrs).get('value')
        name = dict(attrs).get('name')
        if name == '_xsrf' and tag == 'input' and xsrf:
            self.value = xsrf


class WorkOrder:
    def __init__(self, work_order):
        self._work_order = work_order
        self.current_consumable = None
        self.current_producible = None
        self.number = work_order['work_order']['station']
        self.consumable = work_order['consumables']
        self.producible = {}
        for item in work_order['items']:
            self.producible.setdefault(
                item['consumable_part_number'], []
            ).append([{item['consume_qty']: i + 1} for i in range(item['qty'])])
        self.producible_combos = self._all_combos(*self.producible)

    def least_waste(self):
        pass

    def next(self):
        pass

    @staticmethod
    def _all_combos(*data):
        for i in range(1, len(data) + 1):
            for sub_data in itertools.combinations(data, i):
                for elem in itertools.product(*sub_data):
                    yield elem

    def __repr__(self):
        return "<WorkOrder %s>" % repr(self._work_order)

    def __str__(self):
        return str(self._work_order)
