import io
import json
import os
from urllib import request
from zipfile import ZipFile

from flask import Blueprint, current_app, send_from_directory
from flask.helpers import make_response

MODULE_DIR = 'unzip'
INDEX_JSON = 'index.json'

blueprint = Blueprint('unzip', __name__, url_prefix='/unzip')


@blueprint.route('/<uid>')
def unzip(uid):
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
    index_file = os.path.join(uid_dir, INDEX_JSON)

    # file already exist ?
    if os.path.exists(index_file):
        return index_file

    # unzip url to directory
    # TODO: handle http errors and map them to relevant errors to our users
    url = current_app.config['LINKER_URL'] + uid
    conn = request.urlopen(url)
    zipstream = io.BytesIO(conn.read())
    with ZipFile(zipstream) as zipfile:
        for info in zipfile.infolist():
            zipfile.extract(info, path=uid_dir)

    # list files in directory
    files = []
    for file in os.listdir(uid_dir):
        if not file.startswith("."):
            path = os.path.join(uid_dir, file)
            files.append({
                'path': path,
                'size': os.path.getsize(path)
            })

    # dump list to index json
    with open(index_file, 'w') as out:
        json.dump(files, out)

    return index_file
