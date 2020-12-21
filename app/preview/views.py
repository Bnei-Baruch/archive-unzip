import os
import tempfile
import uuid

from flask import Blueprint, current_app, send_file, request

from app.doc2html.views import process_html_path

htmlByBLobBlueprint = Blueprint('doc2htmlByBLob', __name__)


@htmlByBLobBlueprint.route("/doc2htmlByBLob", methods=["POST"])
def doc_2_html_from_bLob():
    print("doc_2_html_from_bLob request {0}", request)
    docx_path = save_to_docx(request.files["doc"])
    print("doc_2_html_from_bLob  docx_path: {1}", docx_path)
    html_path = process_html_path(docx_path)
    print("doc_2_html_from_bLob  docx_path: {1}", html_path)
    current_app.sendfile.send_file(html_path)


def save_to_docx(docx):
    name = str(uuid.uuid4()) + ".docx"
    path = os.path.join(tempfile.TemporaryDirectory(), name)
    docx.save(path)
    return path


def send_html(doc=None):
    if doc is None:
        return
    f = tempfile.TemporaryDirectory()
    send_file(f)
    f.close()
