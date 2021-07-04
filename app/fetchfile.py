import os

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

    def fetch_doc(self, uid, outdir):
        if not self.file_is_doc(uid):
            return Exception
        url = self._linker_url + uid
        r = requests.get(url, allow_redirects=True)
        name = r.url.split('/')[-1]
        out_path = os.path.join(outdir, name)
        with open(out_path, 'wb') as f:
            f.write(r.content)
        return docx.Document(out_path)

    def file_is_doc(self, fuid):
        with self.app.mdb.get_cursor() as cur:
            sql = ('select uid, name, type '
                   'from files where uid = (%s)' % fuid)
            cur.execute(sql)
            row = cur.fetchone()
            if not row or row['type'] != 'text':
                return False
        return True
