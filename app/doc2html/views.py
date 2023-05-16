import os
import re
import shutil
import tempfile
from urllib import request
from collections import namedtuple

from flask import Blueprint, current_app
from flask.helpers import make_response
from flask import jsonify

from .conversionFunctions import doc_to_docx, docx_to_html, docx_to_text

MODULE_DIR = 'doc2html'

htmlBlueprint = Blueprint('doc2html', __name__, url_prefix='/doc2html')
docxBlueprint = Blueprint('doc2docx', __name__, url_prefix='/doc2docx')
textBlueprint = Blueprint('doc2text', __name__, url_prefix='/doc2text')
prepareBlueprint = Blueprint('prepare', __name__, url_prefix='/prepare')


@prepareBlueprint.route('/<uidOrUids>')
def prepare(uidOrUids):
    if not is_single_or_many_uid(uidOrUids):
        return make_response(
            'Expected single or many uids, got [%s].' % uidOrUids, 400)
    uids = uidOrUids.split(',')
    paths, codes = process_docx_uid(uids)
    return jsonify([{'code': code, 'message': '' if code == 200 else msg}
                    for (code, msg) in zip(codes, paths)])


@textBlueprint.route('/<uid>')
def doc2text(uid):
    if not is_single_uid(uid):
        return make_response('Expected single uid, got [%s].' % uid, 400)
    [docx_path], [code] = process_docx_uid([uid])
    if not docx_path or code != 200:
        return make_response('Failed preparing uid: [%s].' % docx_path, code)
    text = docx_to_text(docx_path)
    return make_response(text, code)


@htmlBlueprint.route('/<uid>')
def doc2html(uid):
    if not is_single_uid(uid):
        return make_response('Expected single uid, got [%s].' % uid, 400)
    [docx_path], [code] = process_docx_uid([uid])
    if not docx_path or code != 200:
        return make_response('Failed preparing uid: [%s].' % docx_path, code)
    # TODO: Add try catch here and properly return error.
    html_path = process_html_path(docx_path)
    if not html_path:
        return make_response('missing info', 404)
    return current_app.sendfile.send_file(html_path)


@docxBlueprint.route('/<uid>')
def doc2docx(uid):
    if not is_single_uid(uid):
        return make_response('Expected single uid, got [%s].' % uid, 400)
    [docx_path], [code] = process_docx_uid([uid])
    if not docx_path or code != 200:
        return make_response('Failed preparing uid: [%s].' % docx_path, code)
    return current_app.sendfile.send_file(docx_path)


def is_single_or_many_uid(uid):
    return re.match(r'([a-zA-Z0-9]+)(,([a-zA-Z0-9]+))*', uid)


def is_single_uid(uid):
    return re.match(r'^[a-zA-Z0-9]+$', uid)


def get_dir(uid):
    base_dir = current_app.config['BASE_DIR']
    output_dir = os.path.join(base_dir, MODULE_DIR)
    # Directory example: output_dir/U3/U3d812xj
    uid_dir = os.path.join(output_dir, uid[:2], uid)
    return uid_dir


def get_and_create_dir(uid):
    uid_dir = current_app.fetchfile.get_dir(uid, MODULE_DIR)
    os.makedirs(uid_dir, exist_ok=True)
    return uid_dir


# Helper tuple for process_docx_uid
Move = namedtuple('Move', ['src', 'dest'])


# Download files to one directory.
# Converts doc to docx if needed.
# Moves files to their directories.
# Returns the destination docx paths.
def process_docx_uid(uids):
    if not len(uids):
        return []

    with tempfile.TemporaryDirectory() as temp_dir:
        # Store here pairs of src and dest to move later.
        move_list = [[] for _ in range(len(uids))]
        # List of required conversions from doc to docx.
        doc_to_docx_list = [None]*len(uids)
        ret = [None]*len(uids)
        codes = [200]*len(uids)

        # Download files to one directory (we need this for docx conversion).
        # Then convert them in this one directory and copy to their own
        # directory.
        # TODO: Consider making this in parallel.
        file_types = get_file_types(uids)
        for idx, uid in enumerate(uids):
            # Get real file type from mdb.
            if not file_types[idx]:
                ret[idx] = 'No file type for %s' % uid
                codes[idx] = 404
                continue

            filename = '{}.{}'.format(uid, file_types[idx])
            dest_docx = os.path.join(
                get_dir(uid),
                filename if file_types[idx] == 'docx' else '%sx' % filename)

            docx_exists = os.path.exists(dest_docx)
            if file_types[idx] == 'doc' and not docx_exists:
                doc_to_docx_list[idx] = filename
            else:
                # The file is docx or dest docx exists.
                ret[idx] = dest_docx
                if docx_exists:
                    continue

            path = os.path.join(temp_dir, filename)
            dest_path = os.path.join(get_dir(uid), filename)

            # Download file if necessary.
            if not os.path.exists(dest_path):
                url = current_app.config['LINKER_URL'] + uid
                # TODO: Handle http errors and map them to relevant errors.
                try:
                    request.urlretrieve(url, path)
                except Exception as e:
                    current_app.logger.error('Cant fetch file %s from CDN. Exception %s' % (uid, e))
                    ret[idx] = 'Failed urlretrieve for %s' % url
                    codes[idx] = 404
                    doc_to_docx_list[idx] = None
                    continue
                else:
                    move_list[idx].append(Move(path, dest_path))

        # Convert doc to docx if necessary.
        docx_list = [None]*len(uids)
        if any([doc is not None for doc in doc_to_docx_list]):
            soffice_bin = current_app.config['SOFFICE_BIN']
            docx_list, code, error = doc_to_docx(
                temp_dir, doc_to_docx_list, soffice_bin, current_app.logger)
            if code != 200:
                for idx, doc in enumerate(doc_to_docx_list):
                    if doc is not None:
                        ret[idx] = error
                        codes[idx] = code
        for idx, docx_fullpath in enumerate(docx_list):
            if docx_fullpath is not None:
                dest = os.path.join(get_dir(uids[idx]),
                                    os.path.basename(docx_fullpath))
                move_list[idx].append(Move(docx_fullpath, dest))
        for idx, moves in enumerate(move_list):
            if len(moves):
                get_and_create_dir(uids[idx])
            for src, dest in moves:
                try:
                    shutil.move(src, dest)
                except Exception as e:
                    current_app.logger.debug(
                        'Directory: %s' % os.listdir(os.path.dirname(src)))
                    raise e
                ret[idx] = dest
        return ret, codes


def process_html_path(docx_path):
    html_file = docx_path[:-4] + 'html'
    if os.path.exists(html_file):
        return html_file
    # Convert docx to html.
    return docx_to_html(docx_path, html_file, current_app.logger)


def get_file_types(uids):
    reverse_index = dict([(uid, idx) for idx, uid in enumerate(uids)])
    file_types = [None]*len(uids)
    with current_app.mdb.get_cursor() as cur:
        sql = ('select uid, name, type '
               'from files where uid in (%s)' %
               ','.join(['\'%s\'' % uid for uid in uids]))
        cur.execute(sql)
        rows = cur.fetchall()
        for d in rows:
            if not d or d['type'] != 'text':
                continue
            file_types[reverse_index[d['uid']]] = d['name'].split('.')[-1]
    return file_types
