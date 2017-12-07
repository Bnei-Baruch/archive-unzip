import os
from urllib import request

from flask import Blueprint, current_app, send_from_directory
from flask.helpers import make_response

from .conversionFunctions import doc_to_docx, docx_to_html

MODULE_DIR = 'doc2html'

blueprint = Blueprint('doc2html', __name__, url_prefix='/doc2html')


@blueprint.route('/<uid>')
def doc2html(uid):
    file_path = process_uid(uid)
    if file_path:
        base_dir = current_app.config['BASE_DIR']
        directory = os.path.dirname(os.path.abspath(base_dir))
        return send_from_directory(directory, file_path)
    else:
        return make_response("missing info", 404)


def process_uid(uid):
    base_dir = current_app.config['BASE_DIR']
    output_dir = os.path.join(base_dir, MODULE_DIR)
    os.makedirs(output_dir, exist_ok=True)

    uid_dir = os.path.join(output_dir, uid)
    html_file = os.path.join(uid, uid + '.html')

    # file already exist ?
    if os.path.exists(html_file):
        return html_file

    # make sure uid_dir exist
    os.makedirs(uid_dir, exist_ok=True)

    # Download file
    # TODO: handle http errors and map them to relevant errors to our users
    # TODO get real filename extension?
    path = os.path.join(uid_dir, uid + '.doc')
    url = current_app.config['LINKER_URL'] + uid
    request.urlretrieve(url, path)

    # Convert doc to docx if necessary
    # TODO skip conversion if already docx
    soffice_bin = current_app.config['SOFFICE_BIN']
    docx_file = doc_to_docx(path, soffice_bin, current_app.logger)
    html_file = docx_file[:-4] + "html"

    # Convert docx to html
    return docx_to_html(docx_file, html_file, current_app.logger)
