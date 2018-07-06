import datetime
import os
import random
import shutil
from subprocess import call

from flask import Blueprint, current_app
from flask.helpers import make_response

MODULE_DIR = 'thumbnail'
THUMB_FILE = 'thumb_orig.jpg'

REPRESENTATIVE_FILE_SQL = """
select f.uid, (round((f.properties->>'duration')::real))::int as duration from files f 
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
        return current_app.sendfile.send_file(file_path)
    else:
        return make_response("missing info", 404)

@blueprint.route('/save', methods=('POST'))
def thumbnail_save():
    uid = request.form['uid']
    candidate = request.form['candidate']

    candidate_file = op.path.join(get_candidates_folder(uid), candidate)
    if not os.path.exists(candidate_file)
        return make_response("missing candidate file for uid", 404);

    thumbnail_file = get_current_thumbnail_file(uid)
    shutil.copyfile(candidate_file, thumbnail_file)

    return make_response("thumbnail saved", 200);

# Get the parent folder path for the uid
def get_uid_folder(uid):
    base_dir = current_app.config['BASE_DIR']
    output_dir = os.path.join(base_dir, MODULE_DIR)
    uid_dir = os.path.join(output_dir, uid)

    return uid_dir

# Get the path to the current thumbnail
def get_current_thumbnail_file(uid):
    return os.path.join(get_uid_folder(uid), THUMB_FILE)

# Get the candidates folder path
def get_candidates_folder(uid):
    return os.path.join(get_uid_folder(uid), '.candidates/')

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
    file_uid, duration = get_representative_file(uid)
    if file_uid is None:
        return None

    # make thumbnail from file
    os.makedirs(uid_dir, exist_ok=True)
    url = current_app.config['LINKER_URL'] + file_uid + ".mp4"

    ss = "00:00:05"
    if duration > 5:
        pos = random.randint(5, min(duration, 5 * 60))
        ss = str(datetime.timedelta(seconds=pos))

    ffmpeg_bin = current_app.config['FFMPEG_BIN']
    call([ffmpeg_bin, '-y',
          "-ss", ss,
          "-i", url,
          "-vf", "thumbnail",
          "-vframes", "1",
          "-format", "image2",
          thumb_file])

    return thumb_file


def get_representative_file(unit_id):
    """ return the file uid from unit uid """
    with current_app.mdb.get_cursor() as cur:
        cur.execute(REPRESENTATIVE_FILE_SQL, (unit_id,))
        d = cur.fetchone()
        return d['uid'], d['duration'] if d else None
