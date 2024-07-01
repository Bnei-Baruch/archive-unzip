from contextlib import contextmanager
from urllib.parse import urlparse

import psycopg2
from psycopg2 import pool, extras


class MDB(object):

    def __init__(self, app=None, pool_size=2):
        self.app = app
        self._pool = None
        self.pool_size = pool_size

        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        url = urlparse(app.config['MDB_URL'])
        #url = urlparse("postgres://mdb:g!7vJx-QHz@pgsql2.mdb.local/mdb?sslmode=disable&user=mdb&password=g!7vJx-QHz")
        # url = urlparse("postgres://pgsql2.mdb.local/mdb?sslmode=disable&user=readonly&password=g!7vJx-QHz")
        self._pool = psycopg2.pool.ThreadedConnectionPool(0, self.pool_size,
                                                          database=url.path[1:],
                                                          user=url.username,
                                                          password=url.password,
                                                          host=url.hostname,
                                                          port=url.port)
        app.mdb = self

    @contextmanager
    def get_connection(self):
        connection = None
        try:
            connection = self._pool.getconn()
            yield connection
        finally:
            if connection is not None:
                self._pool.putconn(connection)

    @contextmanager
    def get_cursor(self):
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            try:
                yield cursor
            finally:
                cursor.close()
