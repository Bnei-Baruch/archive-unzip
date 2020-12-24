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
    if file == None:
        print("doc_2_html_from_bLob non file")
        return make_response("You must send file", 400)
    with tempfile.TemporaryDirectory() as dir_path:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            # return make_response("Can't save file", 500)
        docx_path = save_to_docx(file, dir_path)
        return send_html(docx_path, dir_path)


def send_html(docx_path, dir):
    path = process_html_path(docx_path)
    test_file(path)
    if os.path.isabs(path):
        resp = send_file(path, as_attachment=True, cache_timeout=0)
    else:
        resp = send_from_directory(dir, path)
    print("send_html path: {0}, dir_path: {1}".format(path, dir))
    resp = Sendfile.sendfile_to_accel(resp)
    return resp


def save_to_docx(docx, dir):
    path = os.path.join(dir, docx.filename)
    print("save_to_docx path: {0}, dir_path: {1}".format(path, dir))
    docx.save(path)
    test_file(path)
    return path


def test_file(path):
    f = open(path, 'rb')
    if f is None:
        print("test_file no file")
    print("test_file type {0}, list: {1}".format(type(f), f.readlines()))
