import os
import re
import tempfile

import docx
import requests
from flask import send_file, send_from_directory


class Fetchfile(object):

    def __init__(self, app=None):
        self.app = app
        self._linker_url = None
        self._base_dir = None

        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self._base_dir = self.app.config['BASE_DIR']
        self._linker_url = self.app.config['LINKER_URL']
        app.fetchfile = self

    def fetch_doc(self, uid, get_dir):
        with  self.file_is_doc(uid) as d:
            if d is None:
                raise Exception('MDB Entity File with UID - {} is not document'.format(uid))
            dir_path = get_dir(uid)
            out_path = os.path.exists(os.path.join(dir_path, d['name']))
            if out_path is None:
                out_path = os.path.exists(os.path.join(dir_path, '%sx' % d['name']))
            if out_path is not None:
                return out_path

            url = self._linker_url + uid
            r = requests.get(url, allow_redirects=True)
            name = r.url.split('/')[-1]
            out_path = os.path.join(dir_path, name)
            with open(out_path, 'wb') as f:
                f.write(r.content)
            return out_path

    def file_is_doc(self, fuid):
        d = dict()
        with self.app.mdb.get_cursor() as cur:
            sql = ('select uid, name, type, sha1 '
                   'from files where uid = (%s)' % fuid)
            cur.execute(sql)
            row = cur.fetchone()
            if not row or row['type'] != 'text':
                return None
            return row

    def get_dir(self, uid, module):
        base_dir = self.app.config['BASE_DIR']
        output_dir = os.path.join(base_dir, module)
        # Directory example: output_dir/U3/U3d812xj
        uid_dir = os.path.join(output_dir, uid[:2], uid)
        return uid_dir

