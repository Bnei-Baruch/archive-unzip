#!/usr/bin/python3

import io
import json
import os
from urllib import request
from zipfile import ZipFile

from flask.helpers import make_response

index_json = 'index.json'
app_dir = 'unzip'


def unzip_uid(uid, linker_base_url, base_dir):
    output_dir = os.path.join(base_dir, app_dir) if base_dir else app_dir
    try:
        json_file = process_dir(uid, linker_base_url, output_dir)
        with open(json_file) as filein:
            resp = make_response(filein.read(), 200)
            resp.headers['Content-Type'] = 'application/json'
    except Exception as e:
        resp = make_response('{"error": "%s"}' % str(e), 400)
        resp.headers['Content-Type'] = 'application/json'
    return resp


def process_dir(uid, linker_base_url, output_dir):
    uid_dir = os.path.join(output_dir, uid)
    index_file = os.path.join(uid_dir, index_json)
    if not os.path.exists(index_file):
        unzip_from_link(linker_base_url + uid, uid_dir)
        gen_dir_json(uid_dir, index_file)
    return index_file


def unzip_from_link(url, uid_dir):
    conn = request.urlopen(url)
    zipstream = io.BytesIO(conn.read())
    with ZipFile(zipstream) as zipfile:
        for info in zipfile.infolist():
            zipfile.extract(info, path=uid_dir)


def gen_dir_json(dirname, contents_file):
    files = []
    for file in os.listdir(dirname):
        if not file.startswith("."):
            files.append({
                'path': os.path.join(dirname, file),
                'size': os.path.getsize(os.path.join(dirname, file))
            })
    with open(contents_file, 'w') as out:
        json.dump(files, out)
