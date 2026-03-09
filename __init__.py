import os
import sys
#import threading

import folder_paths
#from werkzeug.middleware.dispatcher import DispatcherMiddleware
from aiohttp_wsgi import WSGIHandler
from aiohttp import web
from server import PromptServer

_plugin_root = os.path.dirname(os.path.realpath(__file__))
if _plugin_root not in sys.path:
    sys.path.insert(0, _plugin_root)

os.environ["BASE_OUTPUT_PATH"] = folder_paths.output_directory
os.environ["BASE_INPUT_PATH"] = folder_paths.input_directory
os.environ["BASE_SMARTGALLERY_PATH"] = folder_paths.output_directory

import smartgallery as sg

WEB_DIRECTORY = "./web"
NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

sg.setup_gallery()
wsgi_app = WSGIHandler(sg.app)


@PromptServer.instance.routes.route("*", "/galleryout{_:.*}")
async def _handle_galleryout(request: web.Request) -> web.StreamResponse:
    request.match_info["path_info"] = request.path
    return await wsgi_app(request)
