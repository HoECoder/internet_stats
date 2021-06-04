"""S"""
try:
    from internet_stats.ping_stats import Pinger
except ImportError:
    pass
except ImportWarning:
    pass
try:
    from internet_stats.speed_stats import Speedtester
except ImportError:
    pass
except ImportWarning:
    pass