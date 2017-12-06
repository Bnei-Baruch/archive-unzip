#!/usr/bin/python3

import os
from subprocess import call
from psycopg2 import connect
from flask.helpers import make_response
from flask import send_file

# db settings
app_dir = 'thumbnail'
db_name = os.environ.get('DB_NAME')
db_user = os.environ.get('DB_USER')
db_pass = os.environ.get('DB_PASS')
db_host = os.environ.get('DB_HOST')


def thumbnail_uid(uid, linker_base_url, base_dir):
    """ create thumbnail from unit id and serve to client """
    try:
        file_uid = get_file_uid(uid)
        uid_dir = os.path.join(base_dir, app_dir, uid)
        png_file = os.path.join(uid_dir, "thumb_orig.png")

        if not os.path.exists(png_file):
            os.makedirs(uid_dir, exist_ok=True)
            call(["ffmpeg", '-y',
                  "-ss", "00:00:15",
                  "-i", linker_base_url + file_uid + ".mp4",
                  "-vf", "thumbnail",
                  "-vframes", "1",
                  "-format", "image2",
                  "-vcodec", "png",
                  png_file])
            resp = send_file(png_file, mimetype='image/png')

    except Exception as e:
        resp = make_response(str(e), 400)
        resp.headers['Content-Type'] = 'text/plain'
        raise e

    return resp


def get_file_uid(unit_id):
    """ return the file uid from unit uid """
    try:
        conn = connect("dbname='{}' user='{}' host='{}' password='{}'".format(db_name, db_user, db_host, db_pass))
        cur = conn.cursor()
        cur.execute("""select f.uid from files f inner join content_units cu on f.content_unit_id = cu.id 
                and cu.uid='{}' and f.secure=0 and f.published is true and f.name ~ '\.mp4$';""".format(unit_id))
        rows = cur.fetchone()
        ret = rows[0]
    except Exception as e:
        raise e
        ret = -1
    return ret





