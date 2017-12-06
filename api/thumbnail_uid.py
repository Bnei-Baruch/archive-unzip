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
    uid_dir = os.path.join(base_dir, app_dir, uid)
    png_file = os.path.join(uid_dir, "thumb_orig.png")

    # compute if necessary
    if not os.path.exists(png_file):

        # find representative video file
        file_uid = get_file_uid(uid)
        if file_uid is None:
            resp = make_response("content unit has no available video file", 400)
            resp.headers['Content-Type'] = 'text/plain'
            return resp

        # make thumbnail from file with ffmpeg
        os.makedirs(uid_dir, exist_ok=True)
        call(["ffmpeg", '-y',
              "-ss", "00:00:15",
              "-i", linker_base_url + file_uid + ".mp4",
              "-vf", "thumbnail",
              "-vframes", "1",
              "-format", "image2",
              "-vcodec", "png",
              png_file])

    return send_file(png_file, mimetype='image/png')


def get_file_uid(unit_id):
    """ return the file uid from unit uid """

    conn = connect(dbname=db_name, user=db_user, host=db_host, password=db_pass)
    cur = conn.cursor()
    cur.execute("""select f.uid from files f inner join content_units cu on f.content_unit_id = cu.id 
            and cu.uid='{}' and f.secure=0 and f.published is true and f.name ~ '\.mp4$';""".format(unit_id))
    rows = cur.fetchone()
    return rows[0] if rows else None
