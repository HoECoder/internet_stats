#!/usr/bin/execlineb
s6-envuidgid nobody
s6-applyuidgid -U
s6-log -bp T 1 n20 s1000000 T /var/log/internet_statistics