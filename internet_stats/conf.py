"""For configs"""

from typing import Iterable, Mapping
import yaml
from pytimeparse import parse as human_duration_parser

DEFAULT_CONF = {
    "speedtest": {
        "servers": [],
        "frequency": "2h"
    },
    "latency": {
        "urls": [
            "aws.amazon.com",
            "www.amazon.com",
            "mail.google.com",
            "www.google.com",
            "1.1.1.1",
            "1.0.0.1",
            "8.8.8.8",
            "8.8.4.4",
            "9.9.9.9"
        ],
        "count": 4,
        "size": 1,
        "frequency": "1h"
    },
    "redis": {
        "addr": "localhost",
        "port": 6379
    }
}

def sanitize_conf(config: Mapping, duration_keys: list):
    def sanitizer(conf: Mapping):
        for key in conf.keys():
            if key in duration_keys:
                conf[key] = human_duration_parser(conf[key])
            val = conf[key]
            if isinstance(val, Mapping):
                sanitizer(val)
    sanitizer(config)

DEFAULT_CONF = sanitize_conf(DEFAULT_CONF, ['frequency'])

class ConfigLoader(dict):
    def __init__(self, conf_file: str, default: Mapping):
        self.conf_file = conf_file
        data = self.load_conf()
        super().__init__(**data)
    def load_conf(self):
        with open(self.conf_file) as yaml_file:
            conf = yaml.safe_load(yaml_file)
            sanitize_conf(conf, ['frequency'])
            #print(conf)
            return conf

