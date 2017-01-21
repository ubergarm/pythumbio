import os

import asyncio
import uvloop
import aiohttp

from sanic import Sanic
from sanic.response import json, HTTPResponse

# configure global settings via environment variables
HEAD_LIMIT = int(os.environ.get('HEAD_LIMIT', (1024 * 1024 * 2)))
NUM_THREADS = int(os.environ.get('NUM_THREADS', 1))
NUM_CONCURRENCY = int(os.environ.get('NUM_CONCURRENCY', 4))

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
loop = asyncio.new_event_loop()
sem = asyncio.Semaphore(NUM_CONCURRENCY)

app = Sanic(__name__)


async def fetch(session, url, auth=None):
    """Fetch the first HEAD_LIMIT bytes of image content"""
    headers = {'Range': 'bytes=0-{}'.format(HEAD_LIMIT)}
    if auth:
        headers['Authorization'] = '{}'.format(auth)

    redir = None
    # aiohttp doesn't strip Authorization headers on 30x redirect, so do it:
    async with session.get(url, headers=headers, allow_redirects=False) as response:
        if response.status == 206:
            return await response.content.read()
        if response.status == 307:
            redir = response.headers.get('Location')
            response.release()

    if redir:
        if auth:
            del headers['Authorization']
        async with session.get(redir, headers=headers, allow_redirects=False) as response:
            return await response.content.read()


async def video(headers, args):
    """Returns a thumbnail extracted from video at specified url"""
    auth = headers.get('Authorization')
    url = args.get('url')
    width = args.get('width', -1)
    height = args.get('height', -1)
    watermark = args.get('watermark')
    alpha = args.get('alpha', 0.5)
    scale = args.get('scale', 0.20)
    offset = args.get('offset', 0.05)

    if watermark:
        cmd = ['ffmpeg',
               '-i', '-',
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
               '-i', '-',
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
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                )

        proc = await create

        async with aiohttp.ClientSession(loop=loop) as session:
            stdout, stderr = await proc.communicate(await fetch(session, url, auth))

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


app.run(host="0.0.0.0", port=8000, loop=loop, workers=NUM_THREADS)
