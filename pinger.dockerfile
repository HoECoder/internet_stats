FROM python:3.8-alpine

WORKDIR /home/ping_stats
COPY requirements-ping.txt requirements-ping.txt
COPY internet_stats internet_stats
COPY pinger.py pinger.py
COPY *.toml ./
RUN rm -rf /home/ping_stats/venv &&\
    rm -rf .git &&\
    pip install -r requirements-ping.txt &&\
    chmod +x /home/ping_stats/pinger.py

ENTRYPOINT ["/home/ping_stats/pinger.py"]