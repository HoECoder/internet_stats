"""D"""
from internet_stats.ping_stats import PingError
import time
import logging
from multiprocessing.connection import Connection
from typing import Mapping
from redis import Redis, RedisError

from pytimeparse import parse as human_duration_parser

from internet_stats import Pinger, Speedtester

_mod_logger = logging.getLogger("runners")

def ping_runner(conf: Mapping, read_pipe: Connection):
    run = True
    pinger = Pinger(conf['latency']['urls'],
                    count=conf['latency']['count'],
                    size=conf['latency']['size'])
    time_of_last_ping = 0
    ping_freq = conf['latency']['frequency']
    while run:
        if read_pipe.poll():
            run = read_pipe.recv()
            if not run:
                break
        now = time.time()
        if time_of_last_ping + ping_freq < now:
            try:
                pinger.ping()
            except PingError as ping_error:
                _mod_logger.error(f"Ping failed: {str(ping_error)}")
                run = False
                break
            result = pinger.result
            if not result:
                continue
            for url, stats in result.items():
                _mod_logger.info(f"{url}: {stats}")
                #print(f"{url}: {stats}")
            try:
                redis = Redis(conf['redis']['addr'])
                for url, stats in result.items():
                    redis.hmset(url, stats)
                del redis
            except RedisError as err:
                _mod_logger.error(f"Hit a redis error: {str(err)}")
                #print(f"Hit a redis error: {str(err)}")
            time_of_last_ping = now
        if read_pipe.poll():
            run = read_pipe.recv()
            if not run:
                break
        time.sleep(30)

def speed_runner(conf: Mapping, read_pipe: Connection, starting_time=0):
    run = True
    if not starting_time:
        init_time = conf['speedtest'].get('initial_delay', None)
        if init_time:
            init_time = human_duration_parser(init_time)
            if init_time:
                starting_time = time.time() + init_time
    if starting_time:
        delay_sec = round(starting_time - time.time(), 0)
        time_s = time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.localtime(starting_time))
        _mod_logger.info(f"Delaying speed test by {delay_sec} seconds, starting around {time_s}")
    time_of_last_test = 0
    print(time_of_last_test, time.time())
    test_freq = conf['speedtest']['frequency']
    servers = conf['speedtest']['servers']
    while run:
        if read_pipe.poll():
            run = read_pipe.recv()
            if not run:
                break
        now = time.time()
        if now < starting_time:
            time.sleep(30)
            continue
        if time_of_last_test + test_freq < now:
            speeder = Speedtester(servers)
            speeder.speed_test()
            result = speeder.result
            if not result:
                continue
            _mod_logger.info(result)
            try:
                redis = Redis(conf['redis']['addr'])
                redis.hmset("speedtest", result)
                time_of_last_test = now
                del redis
            except RedisError as err:
                _mod_logger.error(f"Hit redis error {str(err)}")
                time_of_last_test = now
        else:
            print(f"sleep: {time_of_last_test + test_freq} >= {now}, {(time_of_last_test + test_freq) >= now}")
        if read_pipe.poll():
            run = read_pipe.recv()
            if not run:
                break
        time.sleep(30)
