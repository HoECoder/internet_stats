#!/usr/bin/env python
import logging
import logging.config
import time
from multiprocessing import Pipe, Process
from multiprocessing.connection import Connection
from typing import List, Mapping, Tuple, Union, Iterable

import click
from pytimeparse import parse as human_duration_parser
import yaml

from runners import ping_runner, speed_runner
from internet_stats.conf import ConfigLoader, DEFAULT_CONF

def fire_up_runner(conf: Mapping, runner, extra_args: Union[Iterable, None] = None, kwargs: Union[Mapping, None] = None) -> Tuple[Connection, Process]:
    pipe_a, pipe_b = Pipe()
    args = [conf, pipe_b]
    if extra_args:
        args.extend(extra_args)
    if not kwargs:
        kwargs = {}
    proc = Process(target=runner, args=args, kwargs=kwargs)
    return (pipe_a, proc)

@click.group(chain=True, invoke_without_command=True)
@click.option("-c", "--config", "config", default='config.yml')
@click.pass_context
def cli(ctx: click.Context, config: str):
    ctx.ensure_object(dict)
    conf = ConfigLoader(config, DEFAULT_CONF)
    ctx.obj['conf'] = conf
    if ctx.invoked_subcommand is None:
        pipe_to_ping, ping_proc = fire_up_runner(conf, ping_runner)
        pipe_to_speed, speed_proc = fire_up_runner(conf, speed_runner)
        r_1 = {'pipe': pipe_to_ping, 'proc': ping_proc}
        r_2 = {'pipe': pipe_to_speed, 'proc': speed_proc}
        ctx.obj['runners'] = [r_1, r_2]
    with open('logging_config.yml', 'r') as f:
        config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)

@cli.resultcallback()
@click.pass_context
def stats_runner_callback(ctx: click.Context, runners: List, config):
    if not runners:
        runners = ctx.obj['runners']
    pipes = list()
    procs = list()
    for runner in runners:
        pipes.append(runner['pipe'])
        procs.append(runner['proc'])
    for proc in procs:
        proc.start()
    for proc in procs:
        proc.join()

@cli.command("ping")
@click.pass_context
def ping(ctx: click.Context):
    pipe_to_ping, ping_proc = fire_up_runner(ctx.obj['conf'], ping_runner)
    runner = {'pipe': pipe_to_ping, 'proc': ping_proc}
    ctx.obj['ping'] = runner
    return runner

@cli.command("speed")
@click.option("-d", "--delay", "delay", help="Delay from invokation to start", default='')
@click.pass_context
def speed(ctx: click.Context, delay: str):
    delay_as_seconds = human_duration_parser(delay)
    kwargs = None
    if delay_as_seconds:
        kwargs = {
            "starting_time": time.time() + delay_as_seconds
        }
    pipe_to_speed, speed_proc = fire_up_runner(ctx.obj['conf'], speed_runner, kwargs=kwargs)
    runner = {'pipe': pipe_to_speed, 'proc': speed_proc}
    ctx.obj['speed'] = runner
    return runner

if __name__ == "__main__":
    cli()
    # conf = ConfigLoader('config.yml', DEFAULT_CONF)
    # pipe_to_ping, ping_proc = fire_up_runner(conf, ping_runner)
    # pipe_to_speed, speed_proc = fire_up_runner(conf, speed_runner)
    # ping_proc.start()
    # speed_proc.start()
    # ping_proc.join()
    # speed_proc.join()
    