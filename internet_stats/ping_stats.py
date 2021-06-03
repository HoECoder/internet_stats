"""Provides an interface to get Ping/Latency Statistics"""
import os
import time
import logging
from typing import Mapping, Union
from statistics import pvariance, pstdev, median, mean
from pythonping import ping
from pythonping.executor import ResponseList

_mod_logger = logging.getLogger("ping_stats")

class PingError(Exception):
    """Represents a pinging error"""

class Pinger:
    def __init__(self, urls, count=4, size=1, results_to_save=4):
        self.urls = urls
        self.count = count
        self.size = size
        self.last_results = {}
        self.results_to_save = results_to_save
    def update_last_results(self, now: float, new_results: Mapping[str, dict]):
        """Updates the previous results list, possibly removing the oldest result first"""
        if len(self.last_results) < self.results_to_save:
            self.last_results[now] = new_results
        else:
            keys_in_age = sorted(self.last_results)
            oldest_key = keys_in_age[0]
            del self.last_results[oldest_key]
            self.last_results[now] = new_results
    @property
    def result(self) -> Union[None, Mapping[str, dict]]:
        """The most recent ping result"""
        keys = sorted(self.last_results.keys())
        if not keys:
            return None
        return self.last_results[keys[-1]]
    def ping(self):
        now = time.time()
        try:
            all_results: Mapping[str, ResponseList] = {url: ping(url, count=self.count, size=self.size) for url in self.urls}
        except PermissionError as perm_error:
            euid = os.geteuid()
            if euid != 0:
                _mod_logger.error(f"You must be root to ping")
            else:
                _mod_logger.error(f"{str(perm_error)}")
            raise PingError(f"Was UID {euid}") from perm_error
            return  None
        stat_results = {}
        all_timings = []
        total_packets = 0
        lost_packets = 0
        for url, resp in all_results.items():
            max_ms = resp.rtt_max_ms
            min_ms = resp.rtt_min_ms
            avg_ms = resp.rtt_avg_ms
            timings = [r.time_elapsed_ms for r in resp if r.success]
            total_packets += len(resp)
            lost_packets += (len(resp) - len(timings))
            all_timings.extend(timings)
            var_ms = pvariance(timings)
            stdev_ms = pstdev(timings)
            median_ms = median(timings)
            stat_results[url] = {
                "max": max_ms,
                "min": min_ms,
                "avg": avg_ms,
                "var": var_ms,
                "stdev": stdev_ms,
                "median": median_ms,
                "time": now
            }
        combined = {
            "max": max(all_timings),
            "min": min(all_timings),
            "avg": mean(all_timings),
            "var": pvariance(all_timings),
            "stdev": pstdev(all_timings),
            "median": median(all_timings),
            "time": now
        }
        stat_results["combined"] = combined
        self.update_last_results(now, stat_results)
        return stat_results
