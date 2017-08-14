import os
import re
from sanic import Sanic, exceptions
from sanic.response import json, stream
from sanic.log import log
import asyncio
from functools import wraps


PYTHUMBIO_PORT = int(os.environ.get('PYTHUMBIO_PORT', (8000)))
PYTHUMBIO_WORKERS = int(os.environ.get('PYTHUMBIO_WORKERS', 2))
PYTHUMBIO_CONCURRENCY_PER_WORKER = int(os.environ.get('PYTHUMBIO_CONCURRENCY_PER_WORKER', 4))
PYTHUMBIO_CHUNKSIZE = int(os.environ.get('PYTHUMBIO_CHUNKSIZE', (1024 * 32)))

sem = None

app = Sanic(__name__)


def required_args(*expected_args):
    """Ensure url parameters exist before processing request"""
    def decorator(f):
        @wraps(f)
        async def wrapper(request, *args, **kwargs):
            for expected_arg in expected_args:
                if not request.args.get(expected_arg, None):
                    return json({'Error': '{} parameter is required'.format(expected_arg)})
            response = await f(request, *args, **kwargs)
            return response
        return wrapper
    return decorator


@app.listener('before_server_start')
async def init(sanic, loop):
    global sem
    sem = asyncio.Semaphore(PYTHUMBIO_CONCURRENCY_PER_WORKER, loop=loop)
    log.info('Creating semaphore with max concurrency of {} for this worker thread.'
             .format(PYTHUMBIO_CONCURRENCY_PER_WORKER))


@app.route('/webm')
@required_args('url')
async def webm(request):
    """Stream webm"""
    async def stream_fn(response):
        async with sem:
            cmd = ['ffmpeg',
                   '-v',
                   'quiet',
                   '-i',
                   request.args.get('url'),
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


@app.route('/preview')
@required_args('url')
async def preview(request):
    """Stream webm preview"""
    async def stream_fn(response):
        async with sem:
            cmd = ['ffmpeg',
                   '-v',
                   'quiet',
                   '-i',
                   request.args.get('url'),
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


@app.route('/video')
@app.route('/thumb')
@required_args('url')
async def thumb(request):
    """Return jpg thumbnail with optional watermark"""
    watermark = request.args.get('watermark', None)
    width = request.args.get('width', -1)
    height = request.args.get('height', -1)
    alpha = request.args.get('alpha', 0.5)
    scale = request.args.get('scale', 0.20)
    offset = request.args.get('offset', 0.1)
    log.info(watermark)

    async def stream_fn(response):
        async with sem:
            if watermark:
                cmd = ['ffmpeg',
                       '-v',
                       'quiet',
                       '-i',
                       request.args.get('url'),
                       '-i', watermark,
                       '-ss', '00:00:03',
                       '-frames:v', '1',
                       '-f', 'image2',
                       '-filter_complex',
                       '[1:v]colorchannelmixer=aa={alpha}[translogo]; \
                        [translogo][0:v]scale2ref={scale}*min(iw\,ih):{scale}*min(iw\,ih)[logo1][base]; \
                        [base][logo1]overlay=W-w-{offset}*min(W\,H):H-h-{offset}*min(W\,H)[prev]; \
                        [prev]scale=w={width}:h={height}:force_original_aspect_ratio=decrease[out]'
                       .format(width=width, height=height, alpha=alpha, offset=offset, scale=scale),
                       '-map', '[out]',
                       '-'
                       ]
            else:
                cmd = ['ffmpeg',
                       '-v',
                       'quiet',
                       '-i',
                       request.args.get('url'),
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


@app.route('/meta')
@required_args('url')
async def meta(request):
    """Return ffprobe metadata"""
    async def stream_fn(response):
        async with sem:
            cmd = ['ffprobe',
                   '-v',
                   'quiet',
                   '-i',
                   request.args.get('url'),
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


@app.route('/version')
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
    return json({'Error': '404: {}'.format(request.url)})


app.run(host='0.0.0.0', port=PYTHUMBIO_PORT, workers=PYTHUMBIO_WORKERS)
