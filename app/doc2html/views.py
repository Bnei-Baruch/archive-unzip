import os
from urllib import request

from flask import Blueprint, current_app
from flask.helpers import make_response

from .conversionFunctions import doc_to_docx, docx_to_html

MODULE_DIR = 'doc2html'

blueprint = Blueprint('doc2html', __name__, url_prefix='/doc2html')


@blueprint.route('/<uid>')
def doc2html(uid):
    file_path = process_uid(uid)
    if file_path:
        return current_app.sendfile.send_file(file_path)
    else:
        return make_response("Missing info for uid " + uid, 404)


def process_uid(uid):
    base_dir = current_app.config['BASE_DIR']
    uid_dir = os.path.join(base_dir, MODULE_DIR, uid)
    return get_html(uid_dir, uid)


def get_html(uid_dir, uid):
    html_path = build_file_path(uid_dir, uid, "html")
    if not os.path.exists(html_path):
        docx_path = get_docx_path(uid_dir, uid)
        docx_to_html(docx_path, html_path, current_app.logger)
    return html_path


def get_docx_path(uid_dir, uid):
    docx_path = build_file_path(uid_dir, uid, "docx")

    if not os.path.exists(docx_path):
        os.makedirs(uid_dir, exist_ok=True)

        uid_file_type = get_uid_file_type(uid)

        if uid_file_type == "docx":
            fetch_uid(uid, docx_path)
        elif uid_file_type == "doc":
            doc_path = build_file_path(uid_dir, uid, "doc")

            if not os.path.exists(doc_path):
                fetch_uid(uid, doc_path)
                soffice_bin = current_app.config['SOFFICE_BIN']
                doc_to_docx(doc_path, soffice_bin, current_app.logger)
        else:
            current_app.logger.warn("Invalid file type for uid {}: {}".format(uid, uid_file_type))
            return None

    return docx_path


def get_uid_file_type(uid):
    with current_app.mdb.get_cursor() as cur:
        d = cur.execute("select name, type, sub_type, mime_type from files where uid = %s", (uid,)).fetchone()
        return d['name'].split('.')[-1] if d and d['type'] == 'text' else None


def fetch_uid(uid, path):
    url = current_app.config['LINKER_URL'] + uid
    request.urlretrieve(url, path)  # TODO: handle http errors and map them to relevant errors to our users


def build_file_path(uid_dir, uid, file_type):
    return os.path.join(uid_dir, '{}.{}'.format(uid, file_type))
