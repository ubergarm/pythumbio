pythumbio
===
Generate thumbnail images from video streams in a convenient micro-service.

## Branch
This branch tests using `aiohttp` with `uvloop` event loops. However there are some quirks when using this along with multiple `sanic` workers which come from `multiprocessing` currently.

* [channelcat/sanic 152](https://github.com/channelcat/sanic/issues/152)

## Quick Start
Running:
```bash
docker run --rm -it -p 8000:8000 ubergarm/pythumbio
```

Testing:
```bash
# apt-get install -y httpie || brew install httpie
http "http://localhost:8000/video?url=http://myvideo.com/name.mp4"
```

Building:
```bash
docker build -t ubergarm/pythumbio .
```

## Runtime Configuration
Environment Variable | Description | Default
--- | --- | ---
`HEAD_LIMIT` | *Max number of bytes to download of beginning of video file* | `2 MiB`
`NUM_THREADS` | *How many `sanic` worker threads* | `1`
`NUM_CONCURRENCY` | *How many concurrent requests handled per `sanic` worker threads* | `4`

## API
####  Endpoint: `/version`
Returns the output from `ffmpeg -version`

Argument | Description | Default
--- | --- | ---
`-` | *n/a* | `n/a`

####  Endpoint: `/video`
Returns a `jpeg` format thumbnail from a given video file with optional parameters.

Argument | Description | Default
--- | --- | ---
`url` | *url of video to thumbnail* | `n/a`
`width` | *desired width of output thumbnail* | `-1`
`height` | *desired height of output thumbnail* | `-1`
`watermark` | *url of transparent png watermark image* | `n/a`
`alpha` | *opacity of watermark* | `0.5`
`scale` | *scale factor of watermark* | `0.2`
`offset` | *offset from bottom right corner of watermark* | `0.05`

## Benchmarking
You can use `wrk` and point it at your container directly or use `docker` `links` etc...
```bash
docker run --rm -it williamyeh/wrk -t4 -c400 -d30s "http://172.17.0.2:8000/version"
```
```bash
docker run --rm -it williamyeh/wrk -t4 -c400 -d30s "http://172.17.0.2:8000/video?url=http://myvideo.com/name.mp4"
```

## Style Guide
Run
```bash
flake8 --max-line-length=120 server.py
```

## TODO
- [x] Authorization
- [ ] Add better error checking and return codes
- [ ] Secure against Command Injection attacks
- [x] Add more query parameters for various features
- [x] Environment Variables for Config
- [x] Consider `asyncio.subprocess`
- [ ] Remove dependency on `ubergarm/sanic-alpine`

## Bugs
* Doesn't work if video stream info is at the end of the file.

## References
* [ffmpeg](https://ffmpeg.org/)
* [Alpine Linux](https://alpinelinux.org/)
* [Sanic](https://github.com/channelcat/sanic)
