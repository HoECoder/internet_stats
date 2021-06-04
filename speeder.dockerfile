FROM python:3.8-alpine

WORKDIR /home/ping_stats
COPY . .
RUN rm -rf /home/ping_stats/venv &&\
    pip install -r requirements-speeder.txt &&\
    chmod +x /home/ping_stats/speeder.py

ENTRYPOINT ["/home/ping_stats/speeder.py"]