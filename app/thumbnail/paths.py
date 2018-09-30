
# Module directory name where all thumbnails live.
MODULE_DIR = 'thumbnail'

# Name of the current thumbnail file of each unit.
THUMB_FILE = 'thumb_orig.jpg'

# Candidates dir where all candidates are created.
CANDIDATES_DIR = '.candidates'

# SQL query to fetch the file data enough to get the unit's video file path.
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

def get_uid_folder(uid):
    """ Returns the unit's root thumbnails folder path """
    base_dir = current_app.config['BASE_DIR']
    output_dir = os.path.join(base_dir, MODULE_DIR)
    uid_dir = os.path.join(output_dir, uid)

    return uid_dir

def get_current_thumbnail_file(uid):
    """ Returns the path to the current thumbnail for the unit """
    return os.path.join(get_uid_folder(uid), THUMB_FILE)

def get_candidates_folder(uid):
    """ Returns the candidate thumbnails folder path for the unit """
    return os.path.join(get_uid_folder(uid), CANDIDATES_DIR)

def get_video_file_url(file_uid):
    return current_app.config['LINKER_URL'] + file_uid + ".mp4"

def get_representative_file(uid):
    """ Returns the file uid from unit uid """
    with current_app.mdb.get_cursor() as cur:
        cur.execute(REPRESENTATIVE_FILE_SQL, (uid,))
        data = cur.fetchall()
        return [(row['uid'], row['duration']) for row in data]
