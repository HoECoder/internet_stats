#!/usr/bin/env python

from internet_stats.speed_stats import NoServersError
import sys
import time
import logging
import logging.config
from typing import Mapping
import toml
from redis import Redis, RedisError
import speedtest
from pytimeparse import parse as human_duration_parser
from internet_stats import Speedtester

_mod_logger = logging.getLogger("speeder")

def log_next_test_time(now: float, freq: float):
    future = now + freq
    time_s = time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.localtime(future))
    _mod_logger.info(f"Testing again around {time_s}")

def speed_loop(speed_conf: Mapping, redis_conf: Mapping):
    run = True
    servers = speed_conf['servers']
    time_of_last_test = 0
    initial_delay = speed_conf.get('initial_delay', 0)
    start_time = time.time() + initial_delay
    test_freq = speed_conf['frequency']
    min_sleep = speed_conf.get('min_sleep', 30)
    if initial_delay:
        time_s = time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.localtime(start_time))
        _log_s = f"Delaying speed test by {initial_delay} seconds, starting around {time_s}"
        _mod_logger.info(_log_s)
    else:
        start_time -= 10
    _mod_logger.info(f"Will contact: {repr(servers)}")
    while run:
        now = time.time()
        if now < start_time:
            time.sleep(5)
            continue
        if now >= time_of_last_test + test_freq:
            speeder = Speedtester(servers)
            try:
                _mod_logger.info("Beginning Test")
                speeder.speed_test()
            except NoServersError as err:
                _mod_logger.critical(str(err))
                try:
                    _mod_logger.info("Making best effort")
                    speeder = Speedtester(None)
                    speeder.speed_test()
                except speedtest.SpeedtestException as gen_err:
                    _mod_logger.critical(str(gen_err))
                    continue
            except speedtest.SpeedtestException as err:
                _mod_logger.critical(str(err))
                continue
            result = speeder.result
            if not result:
                _mod_logger.warn(f"No test results from {servers}")
                continue
            time_of_last_test = now
            _mod_logger.info(f"{repr(result)}")
            log_next_test_time(now, test_freq)
            if not redis_conf:
                _mod_logger.info(f"No redis")
                continue
            try:
                redis = Redis(redis_conf['addr'],
                              redis_conf.get('port', 6379))
                for url, stats in result.items():
                    redis.hset(url, stats)
                del redis
            except RedisError as redis_error:
                _mod_logger.error(f"Hit a redis error: {str(redis_error)}")
        time.sleep(min_sleep)

if __name__ == "__main__":
    speed_file = "speeder.toml"
    log_conf = "logging_config.toml"
    with open(speed_file, "r") as _speed_file, open(log_conf) as _log_file:
        logging_conf = toml.load(_log_file)
        logging.config.dictConfig(logging_conf)
        config = toml.load(_speed_file)
        redis_conf = config.get('redis')
        speed_conf = config.get('speedtest')
        if not speed_conf:
            _mod_logger.critical(f"No speedtest configuration in '{speed_file}'")
            sys.exit(1)
        if not redis_conf:
            _mod_logger.warning(f"No redis configuration found in {speed_file}")
        speed_conf['frequency'] = human_duration_parser(speed_conf['frequency'])
        speed_conf['initial_delay'] = human_duration_parser(speed_conf.get('initial_delay', '0s'))
        try:
            speed_loop(speed_conf, redis_conf)
        except KeyboardInterrupt:
            _mod_logger.info("CTRL-C Received")