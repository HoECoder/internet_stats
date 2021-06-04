"""Provides Speed Statistics"""

import time
import json
from copy import deepcopy
from typing import Mapping, Union
import speedtest

def make_nice_server_string(server_info: dict) -> str:
    return json.dumps(server_info)

class SpeedtestError(Exception):
    """General Error for Speed Test"""

class NoServersError(SpeedtestError):
    """Raised when no matching servers are found"""

class Speedtester:
    def __init__(self, servers, results_to_save=4):
        self.servers = servers
        self.results = {}
        self.results_to_save = results_to_save
    def update_results(self, now: float, new_results: Mapping[str, dict]):
        """Updates the revious results, possibly removing the oldest"""
        if len(self.results) < self.results_to_save:
            self.results[now] = new_results
        else:
            keys_in_age = sorted(self.results)
            oldest_key = keys_in_age[0]
            del self.results[oldest_key]
            self.results[now] = new_results
    @property
    def result(self) -> Union[None, Mapping[str, dict]]:
        """The most recent ping result"""
        keys = sorted(self.results.keys())
        if not keys:
            return None
        return self.results[keys[-1]]
    def speed_test(self):
        now = time.time()
        tester = speedtest.Speedtest()
        try:
            reduced = tester.get_servers(servers=deepcopy(self.servers))
        except speedtest.NoMatchedServers as no_match_err:
            msg = f"{str(no_match_err)}: {self.servers}"
            raise NoServersError(msg)
        servers = []
        for server in reduced.values():
            servers.extend(server)
        tester.get_best_server(servers=servers)
        tester.download()
        tester.upload()
        
        results = {
            "time": now,
            "down": tester.results.download,
            "up": tester.results.upload,
            "ping": tester.results.ping,
            "sent": tester.results.bytes_sent,
            "recv": tester.results.bytes_received,
            "server_info": make_nice_server_string(tester.results.server)
        }
        self.update_results(now, results)
        return results