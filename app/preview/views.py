import os
import tempfile

from flask import Blueprint, request, jsonify

from flask.helpers import make_response, send_from_directory
from app.doc2html.views import process_html_path

htmlByBLobBlueprint = Blueprint('doc2htmlByBLob', __name__)


@htmlByBLobBlueprint.route("/doc2htmlByBLob", methods=["POST"])
def doc_2_html_from_blob():
    file = request.files.get('doc')
    return build_response(file)


def build_response(file):
    if file is None:
        return make_response("You must send file", 400)
    with tempfile.TemporaryDirectory() as dir_path:
        docx_path = save_to_docx(file, dir_path)
        return send_html(docx_path)


def send_html(docx_path):
    try:
        path = process_html_path(docx_path)
    except IOError as ex:
        return make_response(ex, 500)
    return make_response(html_to_json(path), 200)


def html_to_json(path):
    html = open(path, 'r').read()
    return jsonify({'html': html})


def save_to_docx(docx, dir):
    path = os.path.join(dir, docx.filename)
    docx.save(path)
    return path
