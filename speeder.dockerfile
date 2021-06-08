FROM python:3.8-alpine

WORKDIR /home/speed_stats
COPY requirements-speeder.txt requirements-speeder.txt
COPY internet_stats internet_stats
COPY speeder.py speeder.py
COPY *.toml ./
RUN rm -rf /home/speed_stats/venv &&\
    rm -rf .git &&\
    pip install -r requirements-speeder.txt &&\
    chmod +x /home/speed_stats/speeder.py

ENTRYPOINT ["/home/speed_stats/speeder.py"]