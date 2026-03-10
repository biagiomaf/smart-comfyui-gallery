import os
import sys

import folder_paths
from a2wsgi import WSGIMiddleware
from aiohttp.client_exceptions import ClientConnectionResetError
from aiohttp_asgi import ASGIResource
from server import PromptServer
import logging

_plugin_root = os.path.dirname(os.path.realpath(__file__))
if _plugin_root not in sys.path:
    sys.path.insert(0, _plugin_root)

os.environ["BASE_OUTPUT_PATH"] = folder_paths.output_directory
os.environ["BASE_INPUT_PATH"] = folder_paths.input_directory
os.environ["BASE_SMARTGALLERY_PATH"] = folder_paths.output_directory

WEB_DIRECTORY = "./web"
NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

# sg for smartgallery
import smartgallery as sg
sg.setup_gallery(scan_folders=False)


async def galleryout_asgi(scope, receive, send):
    if scope.get("type") == "http":
        scope = dict(scope)
        scope["root_path"] = ""
    async def safe_send(message):
        try:
            await send(message)
        except ClientConnectionResetError as e:
            logging.debug(f"ClientConnectionResetError: {e}", exc_info=True)

    return await WSGIMiddleware(sg.app)(scope, receive, safe_send)


PromptServer.instance.app.router.register_resource(ASGIResource(galleryout_asgi, root_path="/galleryout"))  