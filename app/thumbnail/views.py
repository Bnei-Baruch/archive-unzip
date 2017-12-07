import os
from subprocess import call

from flask import Blueprint, current_app
from flask.helpers import make_response, send_from_directory

MODULE_DIR = 'thumbnail'
THUMB_FILE = 'thumb_orig.png'

REPRESENTATIVE_FILE_SQL = """
select f.uid from files f 
inner join content_units cu on f.content_unit_id = cu.id
 and cu.uid = %s
 and f.secure=0 
 and f.published is true 
 and f.name ~ '\.mp4$'
 """

blueprint = Blueprint('thumbnail', __name__, url_prefix='/thumbnail')


@blueprint.route('/<uid>')
def thumbnail(uid):
    file_path = process_uid(uid)
    if file_path:
        base_dir = current_app.config['BASE_DIR']
        directory = os.path.dirname(os.path.abspath(base_dir))
        return send_from_directory(directory, file_path)
    else:
        return make_response("missing info", 404)


def process_uid(uid):
    base_dir = current_app.config['BASE_DIR']
    output_dir = os.path.join(base_dir, MODULE_DIR)
    os.makedirs(output_dir, exist_ok=True)

    uid_dir = os.path.join(output_dir, uid)
    thumb_file = os.path.join(uid_dir, THUMB_FILE)

    # file already exist ?
    if os.path.exists(thumb_file):
        return thumb_file

    # find representative video file
    file_uid = get_file_uid(uid)
    if file_uid is None:
        return None

    # make thumbnail from file
    os.makedirs(uid_dir, exist_ok=True)
    url = current_app.config['LINKER_URL'] + file_uid + ".mp4"
    ffmpeg_bin = current_app.config['FFMPEG_BIN']
    call([ffmpeg_bin, '-y',
          "-ss", "00:00:15",
          "-i", url,
          "-vf", "thumbnail",
          "-vframes", "1",
          "-format", "image2",
          "-vcodec", "png",
          thumb_file])

    return thumb_file


def get_file_uid(unit_id):
    """ return the file uid from unit uid """
    with current_app.mdb.get_cursor() as cur:
        cur.execute(REPRESENTATIVE_FILE_SQL, (unit_id,))
        d = cur.fetchone()
        return d['uid'] if d else None
