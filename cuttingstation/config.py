import os
import yaml


class Entry:
    def __init__(self, value, validate):
        """
        Configuration entry object
        :param value: The default value that should be loaded
        :param validate: Value validation method
        """
        self.value = value
        self.validate = validate


class BaseConfig:
    def __init__(self, skeleton):
        """
        Load config.yaml and verify loaded types and load defaults for missing items
        :param skeleton: A dictionary of Entry objects
        :param section: Section of the config file to load
        """
        base = os.path.dirname(os.path.dirname(__file__))
        file_name = os.path.join(base, 'config.yaml')
        try:
            with open(file_name, 'r') as f:
                self._config = yaml.load(f)
        except IOError:
            self._config = {}

        self.__load_config(skeleton)

    def __load_config(self, skeleton):
        """
        :param skeleton: A dictionary of Entry objects
        """
        if self._config is None:
            self._config = {}

        for k in skeleton:
            value = self._config.setdefault(k, skeleton[k].value)
            if not skeleton[k].validate(value):
                # Raise an error if the user provided value is not the correct data type
                raise TypeError('Error loading %s' % k)
            if type(skeleton[k]) == dict:
                # Traverse nested dictionaries
                self.__load_config(skeleton[k])


class Config(BaseConfig):
    def __init__(self):
        BaseConfig.__init__(
            self,
            {'username': Entry('', lambda x: type(x) == str and x != ''),
             'password': Entry('', lambda x: type(x) == str and x != ''),
             'server': Entry('sss.borderstates.com', lambda x: type(x) == str),
             'port': Entry(443, lambda x: type(x) == int or type(x) == str),
             'protocol': Entry('https', lambda x: type(x) == str and x == 'https' or x == 'http'),
             'debug': Entry(False, lambda x: type(x) == bool)}
        )
        self.username = self._config['username']
        self.password = self._config['password']
        self.server = self._config['server'][:-1] if self._config['server'] == '/' else self._config['server']
        self.protocol = self._config['protocol']
        self.port = self._config['port']
        self.url = "%s://%s:%s" % (self.protocol, self.server, self.port)
        self.debug = self._config['debug']
