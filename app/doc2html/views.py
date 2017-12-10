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
        return make_response("missing info", 404)


def process_uid(uid):
    base_dir = current_app.config['BASE_DIR']
    output_dir = os.path.join(base_dir, MODULE_DIR)
    os.makedirs(output_dir, exist_ok=True)

    uid_dir = os.path.join(output_dir, uid)
    html_file = os.path.join(uid_dir, uid + '.html')

    # file already exist ?
    if os.path.exists(html_file):
        return html_file

    # make sure uid_dir exist
    os.makedirs(uid_dir, exist_ok=True)

    # get real file type from mdb
    file_type = get_file_type(uid)
    if not file_type:
        return None

    # Download file if necessary
    path = os.path.join(uid_dir, '{}.{}'.format(uid, file_type))
    if not os.path.exists(path):
        url = current_app.config['LINKER_URL'] + uid
        # TODO: handle http errors and map them to relevant errors to our users
        request.urlretrieve(url, path)

    # Convert doc to docx if necessary
    if file_type == 'doc':
        soffice_bin = current_app.config['SOFFICE_BIN']
        path = doc_to_docx(path, soffice_bin, current_app.logger)

    # Convert docx to html
    html_file = path[:-4] + "html"
    return docx_to_html(path, html_file, current_app.logger)


def get_file_type(uid):
    with current_app.mdb.get_cursor() as cur:
        cur.execute("select name, type, sub_type, mime_type from files where uid = %s", (uid,))
        d = cur.fetchone()
        if not d:
            return None

        if d['type'] != 'text':
            return None

        return d['name'].split('.')[-1]
