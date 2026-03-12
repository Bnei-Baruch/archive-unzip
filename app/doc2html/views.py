import os
import re
import shutil
import tempfile
from urllib import request
from collections import namedtuple

from flask import Blueprint, current_app
from flask.helpers import make_response
from flask import jsonify

from .conversionFunctions import doc_to_docx, docx_to_html, docx_to_text, html_to_text, pdf_to_text, is_gibberish, ocr_pdf

MODULE_DIR = 'doc2html'

htmlBlueprint = Blueprint('doc2html', __name__, url_prefix='/doc2html')
docxBlueprint = Blueprint('doc2docx', __name__, url_prefix='/doc2docx')
textBlueprint = Blueprint('doc2text', __name__, url_prefix='/doc2text')
pdf2textBlueprint = Blueprint('pdf2text', __name__, url_prefix='/pdf2text')
html2textBlueprint = Blueprint('html2text', __name__, url_prefix='/html2text')
uid2textBlueprint = Blueprint('uid2text', __name__, url_prefix='/uid2text')
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
    """Convert doc/docx uid to plain text (doc/docx only)."""
    if not is_single_uid(uid):
        return make_response('Expected single uid, got [%s].' % uid, 400)
    file_types = get_file_types([uid])
    if not file_types or not file_types[0]:
        return make_response('File type not found for uid: [%s].' % uid, 404)
    if file_types[0].lower() not in ['doc', 'docx']:
        return make_response('Expected doc/docx file, got: %s' % file_types[0], 400)
    cached = _read_text_cache(uid)
    if cached is not None:
        return make_response(cached, 200)
    [docx_path], [code] = process_docx_uid([uid])
    if not docx_path or code != 200:
        return make_response('Failed preparing uid: [%s].' % docx_path, code)
    text = docx_to_text(docx_path)
    _write_text_cache(uid, text)
    return make_response(text, code)


@pdf2textBlueprint.route('/<uid>')
def pdf2text(uid):
    """Convert PDF uid to plain text."""
    if not is_single_uid(uid):
        return make_response('Expected single uid, got [%s].' % uid, 400)

    file_types = get_file_types([uid])
    if not file_types or not file_types[0]:
        return make_response('File type not found for uid: [%s].' % uid, 404)
    if file_types[0].lower() != 'pdf':
        return make_response(
            'Expected PDF file, got: %s' % file_types[0], 400)

    cached = _read_text_cache(uid)
    if cached is not None:
        return make_response(cached, 200)

    [file_path], [code] = download_file_if_needed([uid], [file_types[0]])
    if not file_path or code != 200:
        return make_response('Failed to download PDF: [%s].' % uid, code)

    text = pdf_to_text(file_path, current_app.logger)
    if not text or is_gibberish(text):
        current_app.logger.info(f'pdftotext unusable for {uid}, trying OCR fallback')
        text = ocr_pdf(file_path, current_app.logger)
    if not text:
        return make_response('Failed to extract text from PDF', 500)

    _write_text_cache(uid, text)
    return make_response(text, 200)


@html2textBlueprint.route('/<uid>')
def html2text(uid):
    """Convert HTML uid to plain text."""
    if not is_single_uid(uid):
        return make_response('Expected single uid, got [%s].' % uid, 400)

    file_types = get_file_types([uid])
    if not file_types or not file_types[0]:
        return make_response('File type not found for uid: [%s].' % uid, 404)
    if file_types[0].lower() not in ['html', 'htm']:
        return make_response(
            'Expected HTML file, got: %s' % file_types[0], 400)

    cached = _read_text_cache(uid)
    if cached is not None:
        return make_response(cached, 200)

    [file_path], [code] = download_file_if_needed([uid], [file_types[0]])
    if not file_path or code != 200:
        return make_response('Failed to download HTML: [%s].' % uid, code)

    text = html_to_text(file_path)
    if not text:
        return make_response('Failed to extract text from HTML', 500)

    _write_text_cache(uid, text)
    return make_response(text, 200)


@uid2textBlueprint.route('/<uid>')
def uid2text(uid):
    """Convert any supported uid to plain text (auto-detects file type)."""
    if not is_single_uid(uid):
        return make_response('Expected single uid, got [%s].' % uid, 400)

    file_types = get_file_types([uid])
    if not file_types or not file_types[0]:
        return make_response('File type not found for uid: [%s].' % uid, 404)

    file_type = file_types[0].lower()

    cached = _read_text_cache(uid)
    if cached is not None:
        return make_response(cached, 200)

    text = None
    code = 200

    if file_type in ['doc', 'docx']:
        [docx_path], [code] = process_docx_uid([uid])
        if not docx_path or code != 200:
            return make_response('Failed preparing uid: [%s].' % docx_path, code)
        try:
            text = docx_to_text(docx_path)
        except Exception as e:
            current_app.logger.error(f'Failed to convert docx to text for {uid}: {e}')
            return make_response('Failed to extract text from docx', 500)

    elif file_type in ['html', 'htm']:
        [file_path], [code] = download_file_if_needed([uid], [file_type])
        if not file_path or code != 200:
            return make_response('Failed to download HTML: [%s].' % uid, code)
        try:
            text = html_to_text(file_path)
        except Exception as e:
            current_app.logger.error(f'Failed to convert HTML to text for {uid}: {e}')
            return make_response('Failed to extract text from HTML', 500)

    elif file_type == 'pdf':
        [file_path], [code] = download_file_if_needed([uid], [file_type])
        if not file_path or code != 200:
            return make_response('Failed to download PDF: [%s].' % uid, code)
        try:
            text = pdf_to_text(file_path, current_app.logger)
            if not text or is_gibberish(text):
                current_app.logger.info(f'pdftotext unusable for {uid}, trying OCR fallback')
                text = ocr_pdf(file_path, current_app.logger)
            if not text:
                return make_response('Failed to extract text from PDF', 500)
        except Exception as e:
            current_app.logger.error(f'Failed to convert PDF to text for {uid}: {e}')
            return make_response('Failed to extract text from PDF', 500)
    else:
        return make_response(f'Unsupported file type: {file_type}', 400)

    if text:
        _write_text_cache(uid, text)

    return make_response(text if text else '', code)


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


# ---------------------------------------------------------------------------
# Text cache helpers
# ---------------------------------------------------------------------------

def _read_text_cache(uid):
    """Return cached text string, or None if not cached / unreadable."""
    uid_dir = get_and_create_dir(uid)
    cache_path = _safe_join(uid_dir, f'{uid}.txt')
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            current_app.logger.error(f'Failed to read text cache for {uid}: {e}')
    return None


def _write_text_cache(uid, text):
    """Cache text to disk. Errors are non-fatal."""
    uid_dir = get_and_create_dir(uid)
    cache_path = _safe_join(uid_dir, f'{uid}.txt')
    try:
        with open(cache_path, 'w', encoding='utf-8') as f:
            f.write(text)
    except Exception as e:
        current_app.logger.warning(f'Failed to write text cache for {uid}: {e}')


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_join(base_dir, *parts):
    """Join path parts and verify the result stays within base_dir.

    Raises ValueError if the resolved path escapes base_dir, preventing
    path traversal attacks where user-controlled input contains sequences
    like '../../' or null bytes.
    """
    real_base = os.path.realpath(base_dir)
    path = os.path.realpath(os.path.join(base_dir, *parts))
    if not path.startswith(real_base + os.sep) and path != real_base:
        raise ValueError(f'Path traversal detected: {path!r}')
    return path


def is_single_or_many_uid(uid):
    return re.match(r'([a-zA-Z0-9]+)(,([a-zA-Z0-9]+))*', uid)


def is_single_uid(uid):
    return re.match(r'^[a-zA-Z0-9]+$', uid)


def get_dir(uid):
    base_dir = current_app.config['BASE_DIR']
    output_dir = os.path.join(base_dir, MODULE_DIR)
    # Directory example: output_dir/U3/U3d812xj
    uid_dir = _safe_join(output_dir, uid[:2], uid)
    return uid_dir


def get_and_create_dir(uid):
    base_dir = current_app.config['BASE_DIR']
    uid_dir = current_app.fetchfile.get_dir(uid, MODULE_DIR)
    # Ensure the constructed path stays within BASE_DIR
    _safe_join(base_dir, os.path.relpath(uid_dir, base_dir))
    os.makedirs(uid_dir, exist_ok=True)
    return uid_dir


def download_file_if_needed(uids, file_types):
    """Download files (HTML/PDF) if not already cached. Returns (paths, codes)."""
    paths = [None] * len(uids)
    codes = [200] * len(uids)

    for idx, uid in enumerate(uids):
        if not file_types[idx]:
            paths[idx] = 'No file type for %s' % uid
            codes[idx] = 404
            continue

        filename = '{}.{}'.format(uid, file_types[idx])
        uid_dir = get_and_create_dir(uid)
        dest_path = _safe_join(uid_dir, filename)

        # Return cached file if it exists
        if os.path.exists(dest_path):
            paths[idx] = dest_path
            continue

        # Download file from CDN
        url = current_app.config['LINKER_URL'] + uid
        temp_path = dest_path + '.tmp'
        try:
            request.urlretrieve(url, temp_path)

            # The CDN may return a redirect page instead of the actual file:
            #   <a href="https://files.kabbalahmedia.info/get/...">Found</a>.
            # Detect this by checking whether the downloaded content is a
            # small HTML redirect rather than the expected file.
            file_size = os.path.getsize(temp_path)
            if file_size < 1024:
                with open(temp_path, 'rb') as f:
                    first_bytes = f.read(512)
                text = first_bytes.decode('utf-8', errors='ignore')
                if text.strip().startswith('<a href=') and 'files.kabbalahmedia.info' in text:
                    match = re.search(r'<a href="([^"]+)">', text)
                    if not match:
                        raise Exception('Could not extract redirect URL from CDN response')
                    actual_url = match.group(1)
                    current_app.logger.info(f'Following CDN redirect for {uid}: {actual_url}')
                    os.remove(temp_path)
                    request.urlretrieve(actual_url, temp_path)

            shutil.move(temp_path, dest_path)
            paths[idx] = dest_path

        except Exception as e:
            current_app.logger.error('Failed to fetch %s from CDN: %s' % (uid, e))
            paths[idx] = 'Failed to download %s' % url
            codes[idx] = 404
            if os.path.exists(temp_path):
                os.remove(temp_path)

    return paths, codes


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
        doc_to_docx_list = [None] * len(uids)
        ret = [None] * len(uids)
        codes = [200] * len(uids)

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
            uid_dir = get_dir(uid)
            dest_docx = _safe_join(
                uid_dir,
                filename if file_types[idx] == 'docx' else '%sx' % filename)

            docx_exists = os.path.exists(dest_docx)
            if file_types[idx] == 'doc' and not docx_exists:
                doc_to_docx_list[idx] = filename
            else:
                # The file is docx or dest docx exists.
                ret[idx] = dest_docx
                if docx_exists:
                    continue

            path = _safe_join(temp_dir, filename)
            dest_path = _safe_join(uid_dir, filename)

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
        docx_list = [None] * len(uids)
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
    file_types = [None] * len(uids)
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
