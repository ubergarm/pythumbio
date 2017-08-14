import os
import re
from sanic import Sanic, exceptions
from sanic.response import json, stream
from sanic.log import log
import asyncio


PYTHUMBIO_PORT = int(os.environ.get('PYTHUMBIO_PORT', (8000)))
PYTHUMBIO_WORKERS = int(os.environ.get('PYTHUMBIO_WORKERS', 2))
PYTHUMBIO_CONCURRENCY_PER_WORKER = int(os.environ.get('PYTHUMBIO_CONCURRENCY_PER_WORKER', 4))
PYTHUMBIO_CHUNKSIZE = int(os.environ.get('PYTHUMBIO_CHUNKSIZE', (1024 * 32)))

sem = None

app = Sanic(__name__)


@app.listener('before_server_start')
async def init(sanic, loop):
    global sem
    sem = asyncio.Semaphore(PYTHUMBIO_CONCURRENCY_PER_WORKER, loop=loop)
    log.info('Creating semaphore with max concurrency of {} for this worker thread.'
             .format(PYTHUMBIO_CONCURRENCY_PER_WORKER))


@app.middleware("request")
async def validate(request):
    url = request.args.get('url', None)
    if not url:
        return json({"Error": "URL parameter is required"})

    # place JWT Authorization header ffmpeg's target url's `?token=` argument
    auth = request.headers.get('Authorization', None)
    token = None
    if auth:
        try:
            token = re.match(r'Bearer\s+(.*)', auth).group(1)
        except:
            token = None
    if token:
        url += '?token={}'.format(token)

    request['url'] = url


@app.route("/webm")
async def webm(request):
    """Stream webm"""
    async def stream_fn(response):
        async with sem:
            cmd = ['ffmpeg',
                   '-v',
                   'quiet',
                   '-i',
                   request['url'],
                   '-c:v',
                   'libvpx-vp9',
                   '-b:v',
                   '256k',
                   '-tile-columns',
                   '6',
                   '-frame-parallel',
                   '1',
                   '-threads',
                   '2',
                   '-deadline',
                   'realtime',
                   '-speed',
                   '5',
                   '-lag-in-frames',
                   '1',
                   '-vf',
                   'scale=w=426:h=240:force_original_aspect_ratio=decrease',
                   '-c:a',
                   'libvorbis',
                   '-b:a',
                   '64k',
                   '-f',
                   'webm',
                   '-'
                   ]

            proc = await asyncio.create_subprocess_exec(*cmd,
                                                        stdout=asyncio.subprocess.PIPE
                                                        )
            while True:
                chunk = await proc.stdout.read(PYTHUMBIO_CHUNKSIZE)
                if not chunk:
                    break
                response.write(chunk)

    return stream(stream_fn, content_type='video/webm')


@app.route("/preview")
async def preview(request):
    """Stream webm preview"""
    async def stream_fn(response):
        async with sem:
            cmd = ['ffmpeg',
                   '-v',
                   'quiet',
                   '-i',
                   request['url'],
                   '-c:v',
                   'libvpx-vp9',
                   '-b:v',
                   '256k',
                   '-tile-columns',
                   '6',
                   '-frame-parallel',
                   '1',
                   '-threads',
                   '2',
                   '-deadline',
                   'realtime',
                   '-speed',
                   '5',
                   '-lag-in-frames',
                   '1',
                   '-vf',
                   'select=isnan(prev_selected_t)+gt(t-prev_selected_t\,4),setpts=(1/10)*PTS,scale=w=426:h=240:force_original_aspect_ratio=decrease',
                   '-an',
                   '-f',
                   'webm',
                   '-'
                   ]

            proc = await asyncio.create_subprocess_exec(*cmd,
                                                        stdout=asyncio.subprocess.PIPE
                                                        )
            while True:
                chunk = await proc.stdout.read(PYTHUMBIO_CHUNKSIZE)
                if not chunk:
                    break
                response.write(chunk)

    return stream(stream_fn, content_type='video/webm')


@app.route("/video")
@app.route("/thumb")
async def thumb(request):
    """Return jpg thumbnail"""
    async def stream_fn(response):
        async with sem:
            cmd = ['ffmpeg',
                   '-v',
                   'quiet',
                   '-i',
                   request['url'],
                   '-vf',
                   'select=(isnan(prev_selected_t)*gt(t\,2.0))+gt(scene\,0.5),scale=w=426:h=240:force_original_aspect_ratio=decrease,tile=1x1',
                   '-frames:v',
                   '1',
                   '-f',
                   'image2',
                   '-'
                   ]

            proc = await asyncio.create_subprocess_exec(*cmd,
                                                        stdout=asyncio.subprocess.PIPE
                                                        )
            while True:
                chunk = await proc.stdout.read(PYTHUMBIO_CHUNKSIZE)
                if not chunk:
                    break
                response.write(chunk)

    return stream(stream_fn, content_type='image/jpeg')


@app.route("/meta")
async def meta(request):
    """Return ffprobe metadata"""
    async def stream_fn(response):
        async with sem:
            cmd = ['ffprobe',
                   '-v',
                   'quiet',
                   '-i',
                   request['url'],
                   '-print_format',
                   'json',
                   '-show_format',
                   '-show_streams'
                   ]

            proc = await asyncio.create_subprocess_exec(*cmd,
                                                        stdout=asyncio.subprocess.PIPE
                                                        )
            while True:
                chunk = await proc.stdout.read(PYTHUMBIO_CHUNKSIZE)
                if not chunk:
                    break
                response.write(chunk)

    return stream(stream_fn, content_type='application/json')


@app.route("/version")
async def version(request):
    """Return the output of `ffmpeg -version`"""
    async def stream_fn(response):
        async with sem:
            proc = await asyncio.create_subprocess_exec('ffmpeg',
                                                        '-version',
                                                        stdout=asyncio.subprocess.PIPE,
                                                        )
            response.write('{"ver":"')
            while True:
                chunk = await proc.stdout.read(5)
                if not chunk:
                    break
                response.write(chunk)
            response.write('"}')

    return stream(stream_fn, content_type='application/json')


@app.exception(exceptions.NotFound)
def ignore_404s(request, exception):
    return json({"Error": "404: {}".format(request.url)})


app.run(host="0.0.0.0", port=PYTHUMBIO_PORT, workers=PYTHUMBIO_WORKERS)
