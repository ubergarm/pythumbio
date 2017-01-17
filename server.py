from sanic import Sanic
from sanic.response import json, HTTPResponse
import subprocess as sp


app = Sanic()


@app.route("/video")
async def video(request):
    if not request.args.get('url'):
        return json(body={'error': 'no url paramter found'},
                    status=400)

    p = sp.run(['ffmpeg',
                '-i', request.args.get('url'),
                '-ss', '00:00:03',
                '-vframes', '1',
                '-f', 'image2',
                '-'],
               stdout=sp.PIPE,
               stderr=sp.PIPE)

    if p.returncode:
        return json(body={'stdout': p.stdout,
                          'stderr': p.stderr},
                    status=400)

    mime_type = 'image/jpeg'
    return HTTPResponse(status=200,
                        headers=None,
                        content_type=mime_type,
                        body_bytes=p.stdout)


@app.route("/version")
async def version(request):
    p = sp.run(['ffmpeg', '-version'], stdout=sp.PIPE, stderr=sp.PIPE)
    return json({'stdout': p.stdout,
                 'stderr': p.stderr})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, workers=4)
