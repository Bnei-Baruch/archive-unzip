import io
import json
import os
from urllib import request
from zipfile import ZipFile

from flask import Flask, make_response

app = Flask(__name__)
linker_base_url = 'https://cdn.kabbalahmedia.info/'
contents_json = 'contents.json'
output_dir = 'target/assets/sketches'


@app.route('/uid/<uid>')
def get_content(uid):
    try:
        json_file = process_dir(uid)
        with open(json_file) as filein:
            resp = make_response(filein.read(), 200)
            resp.headers['Content-Type'] = 'application/json'
    except Exception as e:
        resp = make_response('{error: "%s"}' % str(e), 400)
        resp.headers['Content-Type'] = 'application/json'
    return resp


def gen_dir_json(dirname, contents_file):
    files = []
    for file in os.listdir(dirname):
        if not file.startswith("."):
            files.append({
                'path': os.path.join(dirname, file),
                'size': os.path.getsize(os.path.join(dirname, file))
            })
    with open(contents_file, 'w') as out:
        json.dump(files, out, indent=2)


def unzip_from_link(url, uid_dir):
    conn = request.urlopen(url)
    zipstream = io.BytesIO(conn.read())
    with ZipFile(zipstream) as zipfile:
        for info in zipfile.infolist():
            zipfile.extract(info, path=uid_dir)


def process_dir(uid):
    uid_dir = os.path.join(output_dir, uid)
    contents_file = os.path.join(uid_dir, contents_json)
    if not os.path.exists(contents_file):
        unzip_from_link(linker_base_url + uid, uid_dir)
        gen_dir_json(uid_dir, contents_file)
    return contents_file
