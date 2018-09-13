import os
import shutil
import tempfile
import sys
import pytest
import app
from app.app import create_app
from app.thumbnail import views, paths

flask_app = create_app() 
test_dir_path = os.path.dirname(os.path.realpath(__file__))
shutil.rmtree(os.path.join(test_dir_path, '.candidates/'))

@pytest.fixture
def client():
    db_fd, flask_app.config['DATABASE'] = tempfile.mkstemp()
    flask_app.config['TESTING'] = True
    client = flask_app.test_client()
    
    yield client

    os.close(db_fd)
    os.unlink(flask_app.config['DATABASE'])

def test_get_candidates(client, monkeypatch):
    """Test get candidates"""
    print('--> Start test_get_candidates()')
    print('--> --> curr dir = {0}'.format(test_dir_path))
    # Mockings
    def mock_get_representative_file(unit_id):
        print('--> mock_get_representative_file() unit_id={0}'.format(unit_id))
        return ['unit_11', 55]
    
    def mock_get_candidates_folder(uid):
        print('--> mock_get_candidates_folder() curr dir = {0}'.format(test_dir_path))
        
        print('--> candidates dir = {0}'.format(os.path.join(test_dir_path, '.candidates/')))
        return os.path.join(test_dir_path, '.candidates/')

    def mock_get_video_file_url(file_uid):
        print('--> mock_get_video_file_url() file_uid  = {0}'.format(file_uid))
        return 'test_dummy_url'

    def mock_call_ffmpeg(ffmpeg_bin, thumbnail_time, url, thumbnail_file):
        print('--> mock_call_ffmpeg() thumbnail_time={0}, url={1}, thumb_file={2}'.format(thumbnail_time, url, thumbnail_file))
        with open(thumbnail_file, 'w') as f:
            f.write('jpg_dummy_file={0}'.format(thumbnail_file))
        return 0

    monkeypatch.setattr(app.thumbnail.paths, 'get_representative_file',mock_get_representative_file)
    monkeypatch.setattr(app.thumbnail.paths, 'get_candidates_folder',mock_get_candidates_folder)       
    monkeypatch.setattr(app.thumbnail.paths, 'get_video_file_url',mock_get_video_file_url)       
    monkeypatch.setattr(app.thumbnail.views, 'call_ffmpeg',mock_call_ffmpeg)       

    # test algorithm
    print('--> --> get(/thumbnail/candidates/unit_11')
   
    rv = client.get('/thumbnail/candidates/unit_11')
    print('--> recieved data:{0}'.format(rv.data))
    #assert b'No entries here so far' in rv.data
    #assert True