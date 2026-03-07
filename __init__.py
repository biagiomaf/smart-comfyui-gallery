import io
import os
import sys
import threading
from urllib.parse import unquote

import folder_paths
from aiohttp import web
from server import PromptServer

_plugin_root = os.path.dirname(os.path.realpath(__file__))
if _plugin_root not in sys.path:
    sys.path.insert(0, _plugin_root)

os.environ["BASE_OUTPUT_PATH"] = folder_paths.output_directory
os.environ["BASE_INPUT_PATH"] = folder_paths.input_directory
os.environ["BASE_SMARTGALLERY_PATH"] = folder_paths.output_directory

WEB_DIRECTORY = "./web"
NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

_HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
}

# sg for smartgallery
_sg_module = None
_sg_init_lock = threading.Lock()
_sg_initialized = False


def _get_sg():
    global _sg_module
    if _sg_module is None:
        import importlib

        _sg_module = importlib.import_module("smartgallery")
    return _sg_module


def _ensure_sg_initialized():
    global _sg_initialized
    sg = _get_sg()
    if _sg_initialized:
        return sg
    with _sg_init_lock:
        if not _sg_initialized:
            sg.initialize_gallery()
            _sg_initialized = True
    return sg


def _build_wsgi_environ(request: web.Request, body: bytes) -> dict:
    server_name = request.host.split(":", 1)[0]
    server_port = request.url.port
    if server_port is None:
        server_port = 443 if request.scheme == "https" else 80

    environ = {
        "REQUEST_METHOD": request.method,
        "SCRIPT_NAME": "",
        "PATH_INFO": unquote(request.rel_url.path),
        "QUERY_STRING": request.rel_url.query_string,
        "SERVER_NAME": server_name,
        "SERVER_PORT": str(server_port),
        "SERVER_PROTOCOL": f"HTTP/{request.version.major}.{request.version.minor}",
        "wsgi.version": (1, 0),
        "wsgi.url_scheme": request.scheme,
        "wsgi.input": io.BytesIO(body),
        "wsgi.errors": sys.stderr,
        "wsgi.multithread": True,
        "wsgi.multiprocess": False,
        "wsgi.run_once": False,
        "REMOTE_ADDR": request.remote or "",
    }

    content_type = request.headers.get("Content-Type")
    if content_type is not None:
        environ["CONTENT_TYPE"] = content_type

    content_length = request.headers.get("Content-Length")
    if content_length is not None:
        environ["CONTENT_LENGTH"] = content_length
    elif body:
        environ["CONTENT_LENGTH"] = str(len(body))

    for k, v in request.headers.items():
        key = "HTTP_" + k.upper().replace("-", "_")
        if key in ("HTTP_CONTENT_TYPE", "HTTP_CONTENT_LENGTH"):
            continue
        environ[key] = v

    return environ


async def _handle_galleryout(request: web.Request) -> web.StreamResponse:
    sg = _ensure_sg_initialized()
    body = await request.read()
    environ = _build_wsgi_environ(request, body)

    status_code = 500
    response_headers = []
    prebody = []

    def start_response(status: str, headers: list, exc_info=None):
        nonlocal status_code, response_headers
        status_code = int(status.split(" ", 1)[0])
        response_headers = headers

        def write(data: bytes):
            prebody.append(data)

        return write

    try:
        result_iter = sg.app.wsgi_app(environ, start_response)
    except Exception:
        return web.Response(status=500, text="SmartGallery internal error")

    resp = web.StreamResponse(status=status_code)
    for k, v in response_headers:
        if k.lower() in _HOP_BY_HOP_HEADERS:
            continue
        try:
            resp.headers.add(k, v)
        except Exception:
            pass

    await resp.prepare(request)

    if request.method != "HEAD":
        for chunk in prebody:
            if chunk:
                await resp.write(chunk)
        try:
            for chunk in result_iter:
                if chunk:
                    await resp.write(chunk)
        finally:
            close = getattr(result_iter, "close", None)
            if callable(close):
                close()

    await resp.write_eof()
    return resp


@PromptServer.instance.routes.route("*", "/galleryout")
async def _galleryout_base(request):
    return await _handle_galleryout(request)


@PromptServer.instance.routes.route("*", "/galleryout/{tail:.*}")
async def _galleryout_tail(request):
    return await _handle_galleryout(request)
