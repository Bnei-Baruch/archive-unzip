import os
import shutil
from urllib import request

from flask.helpers import make_response

from api.conversionFunctions import convert_from_doc_to_docx, convert_from_docx_to_html

app_dir = 'doc2html'
test_uid = 'kROl7RLZ'


def doc2html_uid(uid, linker_base_url, base_dir):
    output_dir = os.path.join(base_dir, app_dir) if base_dir else app_dir
    os.makedirs(output_dir, exist_ok=True)

    try:
        html_file = uid_to_html_file(uid, linker_base_url, output_dir)
        print(html_file)
        with open(html_file) as filein:
            resp = make_response(filein.read(), 200)
            resp.headers['Content-Type'] = 'text/html'
    except Exception as e:
        resp = make_response(str(e), 400)
        resp.headers['Content-Type'] = 'text/plain'
        raise e
    return resp


def uid_to_html_file(uid, linker_base_url, output_dir):
    uid_dir = os.path.join(output_dir, uid)
    html_file = os.path.join(output_dir, uid, uid + '.html')
    if not os.path.exists(html_file):
        print(html_file + ' doesnt exist')
        html_file = url_to_html_file(linker_base_url + uid, uid_dir, uid)
    return html_file


def url_to_html_file(url, uid_dir, uid):
    if os.path.exists(uid_dir):
        shutil.rmtree(uid_dir)
    os.makedirs(uid_dir, exist_ok=True)
    # TODO get real filename
    request.urlretrieve(url, os.path.join(uid_dir, uid + '.doc'))
    return convert_to_html(uid_dir, uid)


def convert_to_html(working_dir, uid):
    uid_path = os.path.join(working_dir, uid)
    convert_from_doc_to_docx(working_dir, uid)
    return convert_from_docx_to_html(uid_path)
