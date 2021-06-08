FROM python:3.8-alpine

WORKDIR /home/web
COPY requirements-web.txt requirements-web.txt
COPY webservice.sh webservice.sh
COPY webservice webservice
RUN rm -rf /home/web/venv &&\
    rm -rf .git &&\
    pip install -r requirements-web.txt &&\
    chmod +x /home/web/webservice.sh

EXPOSE 5000
ENTRYPOINT ["/home/web/webservice.sh"]