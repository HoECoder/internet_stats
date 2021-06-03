FROM python:3.8-alpine

ADD https://github.com/just-containers/s6-overlay/releases/download/v2.2.0.1/s6-overlay-amd64-installer /tmp/
RUN chmod +x /tmp/s6-overlay-amd64-installer && /tmp/s6-overlay-amd64-installer /

WORKDIR /home/net_stats
COPY . .
RUN rm -rf /home/net_stats/venv &&\
    mkdir -p /etc/services.d/100-redis/ &&\
    mkdir -p /etc/services.d/110-inet_service/ &&\
    mkdir -p /etc/services.d/120-stat_service/ &&\
    #cp 110-setup-stat-service.sh /etc/cont-init.d/ &&\
    #chmod +x /etc/cont-init.d/110-setup-stat-service.sh &&\
    cp run-redis.sh /etc/services.d/100-redis/run &&\
    cp run-webservice.sh /etc/services.d/110-inet_service/run &&\
    cp run-stat-service.sh /etc/services.d/120-stat_service/run &&\
    #cp log-stat-serivce.sh /etc/services.d/120-stat_service/log/run &&\
    chmod -R +x /etc/services.d/* &&\
    apk add --no-cache redis &&\
    python -m venv venv &&\
    venv/bin/pip install wheel &&\
    venv/bin/pip install -r requirements.txt &&\
    venv/bin/pip install gunicorn &&\
    chmod +x /home/net_stats/internet_statistics.py

EXPOSE 5000
ENTRYPOINT [ "/init" ]