import datetime
import os
import random
import glob
import json
from subprocess import call

from flask import Blueprint, current_app
from flask.helpers import make_response

MODULE_DIR = 'thumbnail'
THUMB_FILE = 'thumb_orig.jpg'

REPRESENTATIVE_FILE_SQL = """
select
  f.uid,
  (round((f.properties ->> 'duration') :: real)) :: int as duration
from files f
  inner join content_units cu on f.content_unit_id = cu.id
                                 and cu.uid = %s
                                 and f.secure = 0
                                 and f.published is true
                                 and f.name ~ '\.mp4$'
order by
  case
  when (f.properties ->> 'video_size' = 'FHD')
    then 1
  when (f.properties ->> 'video_size' = 'HD')
    then 2
  else 3
  end,
coalesce(array_position('{he, ru, en, es}', f.language), 99)
 """

blueprint = Blueprint('thumbnail', __name__, url_prefix='/thumbnail')


@blueprint.route('/<uid>')
def thumbnail(uid):
    file_path = process_uid(uid)
    if file_path:
        return current_app.sendfile.send_file(file_path)
    else:
        return make_response("missing info", 404)

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


@blueprint.route('thumbnail_candidates/<uid>')
def thumbnail_candidates(uid):
    print ('--> start thumbnail_candidates')
  
	# find representative video file
    file_uid, duration = get_representative_file(uid)
    if file_uid is None:
	    print ('No video file found')
	    return None
    print ('video file_uid =', file_uid, 'duration =', duration)
    
    candidates_dir = get_candidates_folder(uid)
    os.makedirs(candidates_dir, exist_ok=True)

    print ('candidates_dir =', candidates_dir)
	
	# get candidate files from dir 
    candidate_files = glob.glob(candidates_dir + '/c_*.jpg')
	
	# create candidate files, if do not exist
    if not candidate_files:
        print ('No candidates found')
        candidate_files = create_candidate_thumbnails(candidates_dir, file_uid, duration)
	
    return json.dumps(candidate_files)


def create_candidate_thumbnails(candidates_dir, file_uid, duration):
    print ('create_candidate_thumbnails: candidates_dir =', candidates_dir)
	
    candidates_files = []
    for index in range(10):
        thumb_file = createThumbFile(candidates_dir, file_uid, duration)
        candidates_files.append(thumb_file)
    return candidates_files


#  file format: c_<offset>.jpg
def createThumbFile(candidates_dir, file_uid, duration):
    print ('--> start createThumbFile. file_uid=', file_uid, 'duration=', duration)
	
    url = get_video_url(file_uid)
    print ('--> --> start createThumbFile. url={0}'.format(url))
    ss = "00:00:05"
    pos = 5
    if duration > 5:
        pos = random.randint(5, min(duration, 5 * 60))
        ss = str(datetime.timedelta(seconds=pos))
      
    thumb_file_name = 'c_' + str(pos) + '.jpg'
    print ('--> --> start createThumbFile. pos={0}  delta={1} file={2}'.format(pos, ss, thumb_file_name))
    thumb_file = os.path.join(candidates_dir, thumb_file_name)
    ffmpeg_bin = current_app.config['FFMPEG_BIN']
    call_ffmpeg(ffmpeg_bin, ss, url, thumb_file)
    print ('created ThumbFile =', thumb_file)

    return thumb_file

def get_video_url(file_uid):
    return current_app.config['LINKER_URL'] + file_uid + ".mp4"

def call_ffmpeg(ffmpeg_bin, ss, url, thumb_file):
    call([ffmpeg_bin, '-y',
          "-ss", ss,
          "-i", url,
          "-vf", "thumbnail",
          "-vframes", "1",
          "-format", "image2",
          thumb_file])

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
    candidates = get_representative_file(uid)
    if not candidates:
        return None

    # make thumbnail from file
    os.makedirs(uid_dir, exist_ok=True)

    ffmpeg_bin = current_app.config['FFMPEG_BIN']
    for file_uid, duration in candidates:
        url = current_app.config['LINKER_URL'] + file_uid + ".mp4"

        ss = "00:00:05"
        if duration > 5:
            pos = random.randint(5, min(duration, 5 * 60))
            ss = str(datetime.timedelta(seconds=pos))

        ret_code = call([ffmpeg_bin, '-y',
                        "-ss", ss,
                        "-i", url,
                        "-vf", "thumbnail",
                        "-vframes", "1",
                        "-format", "image2",
                        thumb_file])
        if ret_code == 0:
            return thumb_file

    return None


def get_representative_file(unit_id):
    """ return the file uid from unit uid """
    with current_app.mdb.get_cursor() as cur:
        cur.execute(REPRESENTATIVE_FILE_SQL, (unit_id,))
<<<<<<< HEAD
        data = cur.fetchall()
        return [(row['uid'], row['duration']) for row in data]
=======
        d = cur.fetchone()
        if d:
            return d['uid'], d['duration']
        return None, 0

>>>>>>> 80b57b7e110b048b4d3db1fd12cea4ce67509433
