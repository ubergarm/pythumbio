FROM ubergarm/sanic-alpine

RUN apk add --no-cache \
    ffmpeg

COPY . /app

WORKDIR /app

CMD python3 server.py
