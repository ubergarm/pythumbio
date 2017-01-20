pythumbio
===
Generate thumbnail images from video streams in a convenient micro-service.

## Quick Start
Running:
```bash
docker run --rm -it -p 8000:8000 ubergarm/pythumbio
```

Testing:
```bash
# apt-get install -y httpie || brew install htpie
http "http://localhost:8000/video?url=http://myvideo.com/name.mp4"
```

Building:
```bash
docker build -t ubergarm/pythumbio .
```

## Configuration
You can tweak some settings including number of worker threads and number of concurrent workers per thread.

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
- [ ] Authorization
- [ ] Error Checking
- [ ] Secure against Command Injection attacks
- [x] Add more query parameters for various features
- [ ] Environment Variables for Config
- [x] Consider `asyncio.subprocess`
- [ ] Remove dependency on `ubergarm/sanic-alpine`

## References
* [ffmpeg](https://ffmpeg.org/)
* [Alpine Linux](https://alpinelinux.org/)
* [Sanic](https://github.com/channelcat/sanic)
