pythumbio
===
Streaming `webm` transcoder plus previews, metadata, and `jpg` thumbnails in a convenient micro-service.

## Quick Start
Running:
```bash
docker run --rm -it -p 8000:8000 ubergarm/pythumbio
```

Testing:
```bash
# apt-get install -y httpie || brew install httpie
http -v http://localhost:8000/meta?url=http://myvideo.com/name.mp4
```

Development:
```bash
docker run --rm -it -v `pwd`:/app --workdir=/app -p 8000:8000 --entrypoint=/bin/sh ubergarm/pythumbio
python3 server.py
```

Building:
```bash
docker build -t ubergarm/pythumbio .
```

## Runtime Configuration
Environment Variable | Description | Default
--- | --- | ---
`PYTHUMBIO_PORT` | *TCP/IP port number on which to listen* | `8000`
`PYTHUMBIO_WORKERS` | *How many `sanic` worker threads* | `2`
`PYTHUMBIO_CONCURRENCY_PER_WORKER` | *How many concurrent requests handled per `sanic` worker threads* | `4`
`PYTHUMBIO_CHUNKSIZE` | *Streaming HTTP Chunked Transfer Encoding size in bytes* | `32 KiB`

## API
####  Endpoint: `/version`
Returns `application/json` output from `ffmpeg -version`

Argument | Description | Default
--- | --- | ---
`-` | *n/a* | `n/a`

####  Endpoint: `/thumb`
Returns `image/jpeg` thumbnail from a beginning of video

Argument | Description | Default
--- | --- | ---
`url` | *source video url* | `n/a`

####  Endpoint: `/webm`
Returns `video/webm` stream

Argument | Description | Default
--- | --- | ---
`url` | *source video url* | `n/a`

####  Endpoint: `/preview`
Returns `video/webm` stream animated gif style preview

Argument | Description | Default
--- | --- | ---
`url` | *source video url* | `n/a`

####  Endpoint: `/meta`
Returns `application/json` stream of `ffprobe` metadata

Argument | Description | Default
--- | --- | ---
`url` | *source video url* | `n/a`

## Style Guide
Run
```bash
flake8 --max-line-length=120 server.py
```

## TODO
- [ ] Proper error handling
- [ ] Parameterize endpoints
- [ ] Watermark thumbnails
- [ ] Proper logger
- [ ] [Authorization](https://github.com/FFmpeg/FFmpeg/blob/5fe2b437023f46394dfd4a4c991aa4a3ac3d8e72/libavformat/http.c#L282-L284)
- [ ] [DRY](https://en.wikipedia.org/wiki/Don%27t_repeat_yourself) Refactor

## Bugs
* `ffmpeg` transcoding can continue despite [losing client connection](https://github.com/channelcat/sanic/blob/e9eca25792737138df0f6fd3afc10096a03e2aa8/sanic/server.py#L198)

## References
* [ffmpeg](https://ffmpeg.org/)
* [Alpine Linux](https://alpinelinux.org/)
* [Sanic](https://github.com/channelcat/sanic)
