import os

from flask import send_file, send_from_directory


class Sendfile(object):

    def __init__(self, app=None):
        self.app = app
        self._base_dir = None
        self._public_path = None

        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self._base_dir = self.app.config['BASE_DIR']
        self._public_path = self.app.config['PUBLIC_PATH']
        app.sendfile = self

    def send_file(self, file_path):
        if os.path.isabs(file_path):
            resp = send_file(file_path)
        else:
            directory = os.path.dirname(os.path.abspath(self._base_dir))
            resp = send_from_directory(directory, file_path)

        resp = self.sendfile_to_accel(resp)

        return resp

    @staticmethod
    def sendfile_to_accel(resp):
        x = resp.headers.get('X-Sendfile', type=str)
        if x:
            resp.headers['X-Accel-Redirect'] = x

        return resp

    def public_path(self, path):
        return path.replace(self._base_dir, self._public_path, 1)
