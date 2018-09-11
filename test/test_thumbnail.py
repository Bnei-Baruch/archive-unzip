import os
import tempfile
import sys
import pytest

#print('********************** __file__={0}    __name__={1:}    __package__={2:}'.format(__file__,__name__,str(__package__)))
test_dir_path = os.path.dirname(os.path.realpath(__file__))
print('current dir={0}'.format(test_dir_path))

from app.app import create_app
#from app.thumbnail.views
#from flask import url_for, request
import app
from app.thumbnail import views
#app = create_app('production')
#print('before app = create_app()')
flask_app = create_app() 
#print('after app = create_app()')

@pytest.fixture
def client():
    db_fd, flask_app.config['DATABASE'] = tempfile.mkstemp()
    flask_app.config['TESTING'] = True
    client = flask_app.test_client()

    #with flask_app.app_context():
        #flask_app.init_db()
        #print('inside app_context')
        #create_app()

    yield client

    os.close(db_fd)
    os.unlink(flask_app.config['DATABASE'])

def test_get_candidates(client, monkeypatch):
    """Get candidates"""
    print('--> Start test_get_candidates()')
    print('--> --> curr dir = {0}'.format(test_dir_path))
    # Mockings
    def mock_get_representative_file(unit_id):
        print('--> mock_get_representative_file() unit_id={0}'.format(unit_id))
        return ['uid_1234', 55]
    
    def mock_get_candidates_folder(uid):
        print('--> mock_get_candidates_folder() curr dir = {0}'.format(test_dir_path))
        
        print('--> candidates dir = {0}'.format(os.path.join(test_dir_path, '.candidates/')))
        return os.path.join(test_dir_path, '.candidates/')

    def mock_get_video_url(file_uid):
        print('--> mock_get_video_url() file_uid  = {0}'.format(file_uid))
        return 'test_dummy_url'

    def mock_call_ffmpeg(ffmpeg_bin, ss, url, thumb_file):
        print('--> mock_call_ffmpeg() ss={0}, url={1}, thumb_file={2}'.format(ss, url, thumb_file))
        with open(thumb_file, 'w') as f:
            f.write('jpg_dummy_file={0}'.format(thumb_file))

    monkeypatch.setattr(app.thumbnail.views, 'get_representative_file',mock_get_representative_file)
    monkeypatch.setattr(app.thumbnail.views, 'get_candidates_folder',mock_get_candidates_folder)       
    monkeypatch.setattr(app.thumbnail.views, 'get_video_url',mock_get_video_url)       
    monkeypatch.setattr(app.thumbnail.views, 'call_ffmpeg',mock_call_ffmpeg)       

    # test algorithm
    print('--> --> get(/thumbnail/thumbnail_candidates/unit_11')
   
    rv = client.get('/thumbnail/thumbnail_candidates/unit_11')
    print('--> recieved data:{0}'.format(rv.data))
    #assert b'No entries here so far' in rv.data
    #assert True