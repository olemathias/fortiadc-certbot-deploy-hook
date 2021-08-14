FROM certbot/certbot:latest

RUN pip install certbot
RUN pip install certbot-pdns

ADD build/docker-entrypoint.sh /opt/docker-entrypoint.sh
ADD build/new_cert.sh /usr/local/bin/new_cert
ADD main.py /opt/main.py
ADD fortiadc.py /opt/fortiadc.py
ADD __init__.py /opt/__init__.py

ENTRYPOINT ["/opt/docker-entrypoint.sh"]
