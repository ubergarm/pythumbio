import os

import asyncio
import uvloop

from sanic import Sanic
from sanic.response import json, HTTPResponse

# configure global settings via environment variables
HEAD_LIMIT = os.environ.get('HEAD_LIMIT', (1024 * 1024 * 2))
NUM_THREADS = os.environ.get('NUM_THREADS', 1)
NUM_CONCURRENCY = os.environ.get('NUM_CONCURRENCY', 4)

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
sem = asyncio.Semaphore(NUM_CONCURRENCY)

app = Sanic(__name__)


async def video(headers, args):
    """Returns a thumbnail extracted from video at specified url"""
    auth = headers.get('auth', '')
    url = args.get('url', -1)
    width = args.get('width', -1)
    height = args.get('height', -1)
    watermark = args.get('watermark')
    alpha = args.get('alpha', 0.5)
    scale = args.get('scale', 0.20)
    offset = args.get('offset', 0.05)

    if watermark:
        cmd = ['ffmpeg',
               '-headers',
               'Authorization: {}\r\nRange: bytes=0-{}\r\n'
               .format(auth, HEAD_LIMIT),
               '-i', url,
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
               '-headers',
               'Authorization: {}\r\nRange: bytes=0-{}\r\n'
               .format(auth, HEAD_LIMIT),
               '-i', url,
               '-ss', '00:00:03',
               '-frames:v', '1',
               '-f', 'image2',
               '-vf',
               'scale=w={width}:h={height}:force_original_aspect_ratio=decrease'
               .format(width=width, height=height),
               '-'
               ]

    async with sem:
        create = asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                )

        proc = await create

        stdout = bytearray()
        while True:
            line = await proc.stdout.readline()
            if not line:
                break
            stdout.extend(line)

        stderr = bytearray()
        while True:
            line = await proc.stderr.readline()
            if not line:
                break
            stderr.extend(line)

        await proc.wait()

        if proc.returncode:
            return json(body={'stdout': bytes(stdout).decode(),
                              'stderr': bytes(stderr).decode()},
                        status=400)

        mime_type = 'image/jpeg'
        return HTTPResponse(status=200,
                            headers=None,
                            content_type=mime_type,
                            body_bytes=stdout)


async def version():
    """Return the output of `ffmpeg -version`"""
    async with sem:
        create = asyncio.create_subprocess_exec('ffmpeg',
                                                '-version',
                                                stdout=asyncio.subprocess.PIPE,
                                                )
        proc = await create

        stdout = bytearray()
        while True:
            line = await proc.stdout.readline()
            if not line:
                break
            stdout.extend(line)

        await proc.wait()

        return json({"version": bytes(stdout).decode()})


@app.route("/video")
async def query_video(request):
    if not request.args.get('url'):
        return json(body={'error': 'no url paramter found'}, status=400)

    return await video(request.headers, request.args)


@app.route("/version")
async def query_version(request):
    return await version()


app.run(host="0.0.0.0", port=8000, workers=NUM_THREADS)
