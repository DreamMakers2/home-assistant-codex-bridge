ARG BUILD_FROM=ghcr.io/home-assistant/base:latest
FROM ${BUILD_FROM}

RUN apk add --no-cache python3 openssl

COPY server.py /server.py
COPY run.sh /run.sh

RUN chmod 755 /run.sh /server.py

CMD ["/run.sh"]
