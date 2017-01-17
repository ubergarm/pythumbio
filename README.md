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

## Style Guide
Run
```bash
flake8 server.py
```

## TODO
- [ ] Authorization
- [ ] Error Checking
- [ ] Secure against Command Injection attacks
- [ ] Add more query parameters for various features
- [ ] Environment Variables for Config
- [ ] Consider `asyncio.subprocess`
- [ ] Remove dependency on `ubergarm/sanic-alpine`

## References
* [ffmpeg](https://ffmpeg.org/)
* [Alpine Linux](https://alpinelinux.org/)
* [Sanic](https://github.com/channelcat/sanic)
