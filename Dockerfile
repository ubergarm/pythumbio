FROM ubergarm/sanic-alpine

RUN apk add --no-cache \
    ffmpeg \
    openssl \
    ca-certificates && \
    pip install aiohttp

COPY . /app

WORKDIR /app

CMD python3 server.py
