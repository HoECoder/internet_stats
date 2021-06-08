#!/usr/bin/env python


import sys
import time
import logging
import logging.config
from typing import Mapping
import toml
from redis import Redis, RedisError
from pytimeparse import parse as human_duration_parser
from internet_stats.ping_stats import PingError
from internet_stats import Pinger

_mod_logger = logging.getLogger("pinger")

def ping_loop(latency_conf: Mapping, redis_conf: Mapping):
    run = True
    pinger = Pinger(latency_conf['urls'],
                    count = latency_conf['count'],
                    size=latency_conf['size'])
    time_of_last_ping = 0
    ping_freq = latency_conf['frequency']
    min_sleep = latency_conf.get('min_sleep', 30)
    while run:
        now = time.time()
        if now >= time_of_last_ping + ping_freq:
            try:
                pinger.ping()
            except PingError as ping_error:
                _mod_logger.error(f"Ping failed: {str(ping_error)}")
                run = False
                break
            result = pinger.result
            if not result:
                continue
            time_of_last_ping = now
            _mod_logger.info(f"{repr(result)}")
            if not redis_conf:
                _mod_logger.info(f"No redis")
                continue
            try:
                redis = Redis(redis_conf['addr'],
                              redis_conf.get('port', 6379))
                for url, stats in result.items():
                    redis.hmset(url, stats)
                del redis
            except RedisError as redis_error:
                _mod_logger.error(f"Hit a redis error: {str(redis_error)}")
        time.sleep(min_sleep)

if __name__ == "__main__":
    latency_file = "pinger.toml"
    log_conf = "logging_config.toml"
    with open(latency_file, "r") as _latency_file, open(log_conf) as _log_file:
        logging_conf = toml.load(_log_file)
        logging.config.dictConfig(logging_conf)
        config = toml.load(_latency_file)
        redis_conf = config.get('redis')
        latency_conf = config.get('latency')
        if not latency_conf:
            _mod_logger.critical(f"No latency configuration in '{latency_file}'")
            sys.exit(1)
        if not redis_conf:
            _mod_logger.warning(f"No redis configuration found in {latency_file}")
        latency_conf['frequency'] = human_duration_parser(latency_conf['frequency'])
        try:
            ping_loop(latency_conf, redis_conf)
        except KeyboardInterrupt:
            _mod_logger.info("CTRL-C Received")