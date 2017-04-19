from multiprocessing import Process
from HTMLParser import HTMLParser
from config import Config
from time import sleep
import requests
import json


class WebClient(Process):
    def __init__(self):
        Process.__init__(self)
        self.config = None
        self.client = None
        self.authenticated = False
        self.last_active = None

    def run(self):
        try:
            self.config = Config()
            self.client = requests.Session()
            self.login()
            while True:
                wo = self.get_work_order()
                if wo != self.last_active:
                    self.get_cuts(wo)
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
                self.authenticated = True
            else:
                self.authenticated = False
        except requests.exceptions.RequestException:
            self.authenticated = False

    def get_work_order(self):
        r = self.get(self.config.url + '/api/v1/wire_station/%s/active_work_order' % self.config.name)
        wo = json.loads(r.text).get('active_work_order', None)
        return wo if wo else None

    def get_cuts(self, work_order):
        r = self.get(self.config.url + '/api/v1/work_order/%s/items' % work_order)
        if r:
            print(r.text)

    def get(self, *args, **kwargs):
        # Use a default timeout of 1 second
        if 'timeout' not in kwargs:
            kwargs['timeout'] = 1

        try:
            r = self.client.get(*args, **kwargs)
            # If access denied, try to login again
            if r.status_code == 401 or not self.authenticated:
                while not self.authenticated:
                    print("Not connected, retrying...")
                    self.login()
                    sleep(3)  # Rate limit login attempts
                r = self.client.get(*args, **kwargs)
        except requests.ConnectionError:
            return None

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
