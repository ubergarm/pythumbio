import asyncio
import uvloop

from sanic import Sanic
from sanic.response import json, HTTPResponse


asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
# limit number of concurrent requests per worker thread semaphores
sem = asyncio.Semaphore(4)

app = Sanic(__name__)


async def video(url, auth, width, height):
    """Returns a thumbnail extracted from video at specified url"""
    async with sem:
        create = asyncio.create_subprocess_exec(
            'ffmpeg',
            '-headers',
            'Authorization: {}\r\nRange: bytes=0-{}\r\n'.format(auth or '', 1024*1024*2),
            '-i', url,
            '-ss', '00:00:03',
            '-frames:v', '1',
            '-f', 'image2',
            '-vf', 'scale=w={}:h={}:force_original_aspect_ratio=decrease'.format(width or -1, height or -1),
            '-',
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
    url = request.args.get('url')
    width = request.args.get('width')
    height = request.args.get('height')
    auth = request.headers.get('Authorization')
    if not url:
        return json(body={'error': 'no url paramter found'}, status=400)

    return await video(url=url, auth=auth, width=width, height=height)


@app.route("/version")
async def query_version(request):
    return await version()


app.run(host="0.0.0.0", port=8000, workers=4)
