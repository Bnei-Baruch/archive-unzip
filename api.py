#!/usr/local/bin/python3

import os

from flask import Flask

from doc2html_uid import doc2html_uid
from unzip_uid import unzip_uid
from thumbnail_uid import thumbnail_uid

app = Flask(__name__)

linker_base_url = os.environ.get('API_LINKER_URL', 'https://cdn.kabbalahmedia.info/')
print("INFO: api linker_base_url: ", linker_base_url)

base_dir = os.environ.get('API_STATIC_BASE_DIR', 'assets')
print("INFO: api base_dir: ", base_dir)


@app.route('/unzip/<uid>')
def unzip(uid):
    return unzip_uid(uid, linker_base_url=linker_base_url, base_dir=base_dir)


@app.route('/doc2html/<uid>')
def doc2html(uid):
    return doc2html_uid(uid, linker_base_url=linker_base_url, base_dir=base_dir)


@app.route('/thumbnail/<uid>')
def thumbnail(uid):
    return thumbnail_uid(uid, linker_base_url=linker_base_url, base_dir=base_dir)


if __name__ == '__main__':
    app.run()
