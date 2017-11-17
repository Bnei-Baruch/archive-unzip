#!/usr/local/bin/python3

import os

from flask import Flask

from api.doc2html_uid import doc2html_uid
from api.unzip_uid import unzip_uid

app = Flask(__name__)

linker_base_url = os.environ.get('API_LINKER_URL', 'https://cdn.kabbalahmedia.info/')
print("INFO: api linker_base_url: ", linker_base_url)

base_dir = os.environ.get('API_STATIC_BASE_DIR', 'assets')
print("INFO: api base_dir: ", base_dir)


@app.route('/unzip/<uid>')
def unzip(uid):
    print("Asdf")
    return unzip_uid(uid, linker_base_url=linker_base_url, base_dir=base_dir)


@app.route('/doc2html/<uid>')
def doc2html(uid):
    print("docAsdf")
    return doc2html_uid(uid, linker_base_url=linker_base_url, base_dir=base_dir)


if __name__ == '__main__':
    app.run()
