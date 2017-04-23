from multiprocessing import Process
from HTMLParser import HTMLParser
from config import Config
from time import sleep
import requests
import json
import logging


class WebClient(Process):
    def __init__(self):
        Process.__init__(self)
        self.log = logging.getLogger()
        self.config = None
        self.client = None
        self.authenticated = False
        self.last_active = None
        self.station = None

    def run(self):
        try:
            self.config = Config()
            self.client = requests.Session()
            self.login()
            while True:
                wo = self.get_work_order()
                if wo != self.last_active:
                    items = self.get_items(wo)
                self.last_active = wo
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

    def get_work_order(self):
        r = self.get('/api/v1/station/%s/active_work_order' % self.station)
        try:
            wo = json.loads(r.text).get('active_work_order', None)
        except (ValueError, AttributeError):
            wo = None
        return wo

    def get_items(self, work_order):
        r = self.get('/api/v1/work_order/%s/items' % work_order)
        try:
            items = json.loads(r.text)
            self.log.debug("Loaded items: %s" % str(items))
        except (ValueError, AttributeError):
            self.log.debug("Failed to load items for work order %s" % work_order)
            items = {}
        return items

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
        except requests.ConnectionError:
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


class XSRF(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.value = None

    def handle_starttag(self, tag, attrs):
        xsrf = dict(attrs).get('value')
        name = dict(attrs).get('name')
        if name == '_xsrf' and tag == 'input' and xsrf:
            self.value = xsrf
