#!/usr/bin/python3

import os
from flask import Flask
from doc2html_uid import doc2html_uid
from unzip_uid import unzip_uid

app = Flask(__name__)
linker_base_url = 'https://cdn.kabbalahmedia.info/'

base_dir = os.environ.get('API_STATIC_BASE_DIR')
print("INFO: api base_dir: [%s]", base_dir)


@app.route('/unzip/<uid>')
def unzip(uid):
    unzip_uid(uid, linker_base_url=linker_base_url, base_dir=base_dir)


@app.route('/doc2html/<uid>')
def doc2html(uid):
    doc2html_uid(uid, linker_base_url=linker_base_url, base_dir=base_dir)
