
from . import paths

import datetime
import os
import random
import glob
import json
from subprocess import call
from shutil import copyfile

from flask import Blueprint, current_app
from flask.helpers import make_response

blueprint = Blueprint('thumbnail', __name__, url_prefix='/thumbnail')

@blueprint.route('/<uid>', methods=['GET'])
def get_thumbnail(uid):
    file_path = process_uid(uid)
    if file_path:
        return current_app.sendfile.send_file(file_path)
    else:
        return make_response("missing info", 404)

@blueprint.route('/candidates/<uid>', methods=['GET'])
def get_thumbnail_candidates(uid):
    print ('start thumbnail_candidates')
	# find representative video file
    file_uid, duration = paths.get_representative_file(uid)
    if file_uid is None:
	    print ('No video file found')
	    return None
    print ('video file_uid =', file_uid, 'duration =', duration)
    
    candidates_dir = paths.get_candidates_folder(uid)
    os.makedirs(candidates_dir, exist_ok=True)

    print ('candidates_dir =', candidates_dir)
	
	# get candidate files from dir 
    candidate_files = glob.glob(candidates_dir + '/c_*.jpg', recursive=False)
	
	# create candidate files, if do they not exist
    if not candidate_files:
        print ('No candidates found')
        candidate_files = create_candidate_thumbnails(candidates_dir, file_uid, duration)

    # prepare the response
    response = { candidates: [] }
    for candidate_file : candidate_files:
        filename = os.path.splitext(os.path.basename(candidate_file))[0]
        response.candidates.append({ candidate: filename, url: candidate_file })
	
    return json.dumps(response)

@blueprint.route('/<uid>', methods=['POST'])
def set_thumbnail(uid):
    print('saving thumbnail')
    data = request.form;
    candidates_dir = paths.get_candidates_folder(uid)
    if not os.path.exists(candidates_dir):
        return make_response("no candidates for uid", 404)

    candidate_file = os.path.normpath(os.path.join(candidates_dir, data.candidate + '.jpg'))
    if os.path.commonprefix([candidates_dir, candidate_file]) != candidates_dir:
        print ("Saving thumbnail with bad candidate: %s" % data.candidate)
        return make_response("really?", 400)

    if not os.path.exists(candidate_file):
        return make_response("bad candidate for uid", 500)

    current_thumbnail_file = paths.get_current_thumbnail_file(uid)
    shutil.copyfile(candidate_file, current_thumbnail_file)

    return make_response(current_thumbnail_file, 200);

def create_candidate_thumbnails(candidates_dir, file_uid, duration):
    print ('create_candidate_thumbnails: candidates_dir =', candidates_dir)
	
    candidates_files = []
    for index in range(10):
        video_url = paths.get_video_file_url(file_uid)
        thumbnail_time = get_random_thumbnail_time(duration)
        thumb_filename = 'c_' + str(thumbnail_time) + '.jpg'
        thumb_file = os.path.join(candidates_dir, thumb_filename)
        ret_code = create_thumb_file(video_url, thumbnail_time, thumb_file)
        if ret_code == 0:
            candidates_files.append(thumb_file)
        else:
            print ("candidate thumbnail was not created, reason: %s" % ret_code)
    return candidates_files

def get_random_thumbnail_time(duration):
    ''' Returns a random time for a thumbnail.

    The returned value is in a "HH:MM:SS" format.
    '''
    min_seconds = 5
    max_seconds = 5 * 60 # 3 minutes
    thumbnail_time = str(datetime.timedelta(seconds=min_seconds))
    if duration > min_seconds:
        pos = random.randint(min_seconds, min(duration, max_seconds))
        thumbnail_time = str(datetime.timedelta(seconds=pos))

    return thumbnail_time

def create_thumb_file(video_url, thumbnail_time, thumbnail_file):
    ''' Creates a random JPG thumbnail from the supplied video file. '''
    ffmpeg_bin = current_app.config['FFMPEG_BIN']
    ret_code = call([ffmpeg_bin, '-y',
          "-ss", thumbnail_time,
          "-i", url,
          "-vf", "thumbnail",
          "-vframes", "1",
          "-format", "image2",
          thumbnail_file])

    return ret_code

def process_uid(uid):
    thumb_file = paths.get_current_thumbnail_file(uid)
    # file already exist ?
    if os.path.exists(thumb_file):
        return thumb_file

    # find representative video file
    candidates = paths.get_representative_file(uid)
    if not candidates:
        return None

    # make sure the unit id directory exists
    uid_dir = os.path.join(output_dir, uid)
    os.makedirs(uid_dir, exist_ok=True)

    # make thumbnail from file
    for file_uid, duration in candidates:
        video_url = paths.get_video_file_url(file_uid)
        thumbnail_time = get_random_thumbnail_time(duration)
        ret_code = create_thumb_file(video_url, thumbnail_time, thumb_file)
        if ret_code == 0:
            return thumb_file

    return None