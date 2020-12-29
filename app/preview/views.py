import os
import tempfile
import time

from flask import Blueprint, current_app, send_file, request

from flask.helpers import make_response, send_from_directory
from app.doc2html.views import process_html_path
from app.sendfile import Sendfile

htmlByBLobBlueprint = Blueprint('doc2htmlByBLob', __name__)


@htmlByBLobBlueprint.route("/doc2htmlByBLob", methods=["POST"])
def doc_2_html_from_bLob():
    file = request.files.get('doc')
    resp = build_response(file)
    resp.headers.add("Access-Control-Allow-Origin", "*")
    resp.headers.add("Access-Control-Expose-Headers", "Content-Length")
    return resp


def build_response(file):
    if file is None:
        return make_response("You must send file", 400)
    with tempfile.TemporaryDirectory() as dir_path:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        docx_path = save_to_docx(file, dir_path)
        return send_html(docx_path)


def send_html(docx_path):
    try:
        path = process_html_path(docx_path)
    except RuntimeError as ex:
        return make_response(ex, 400)
    return current_app.sendfile.send_file(path)


def save_to_docx(docx, dir):
    path = os.path.join(dir, docx.filename)
    docx.save(path)
    return path
