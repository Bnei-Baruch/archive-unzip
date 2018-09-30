import os
import shutil
import tempfile
import sys
import pytest
import app
import json
import random
from app.app import create_app
from app.thumbnail import views, paths

flask_app = create_app() 

# delete candidates dir
test_dir_path = os.path.dirname(os.path.realpath(__file__))
shutil.rmtree(os.path.join(test_dir_path, '.candidates'), True)

#global
mock_randint_value=0

@pytest.fixture
def client():
    db_fd, flask_app.config['DATABASE'] = tempfile.mkstemp()
    flask_app.config['TESTING'] = True
    client = flask_app.test_client()
    
    yield client

    os.close(db_fd)
    os.unlink(flask_app.config['DATABASE'])
    
# Mockings
def mock_get_representative_file(unit_id):
    print('\n--> mock_get_representative_file() unit_id={0}'.format(unit_id))
    return ['unit_11', 55]


def mock_get_candidates_folder(uid):
    print('\n--> mock_get_candidates_folder() curr dir = {0}'.format(test_dir_path))
        
    print('\n--> candidates dir = {0}'.format(os.path.join(test_dir_path, '.candidates')))
    return os.path.join(test_dir_path, '.candidates')

def mock_get_video_file_url(file_uid):
    print('\n--> mock_get_video_file_url() file_uid  = {0}'.format(file_uid))
    return 'test_dummy_url'

def mock_call_ffmpeg(ffmpeg_bin, thumbnail_time, url, thumbnail_file):
    print('\n--> mock_call_ffmpeg() thumbnail_time={0}, url={1}, thumb_file={2}'.format(thumbnail_time, url, thumbnail_file))
    with open(thumbnail_file, 'w') as f:
        f.write('jpg_dummy_file={0}'.format(thumbnail_file))
    return 0
    
def mock_randint(low, high):
    global mock_randint_value
    print('\n--> mock_randint() low={0}  high={1}  randint_return_value={2}'.format(low, high, mock_randint_value))
    current_return = mock_randint_value
    mock_randint_value=mock_randint_value+1
    return current_return    
    
    
def test_get_candidates(client, monkeypatch):
    """Test get candidates"""

    monkeypatch.setattr(app.thumbnail.paths, 'get_representative_file',mock_get_representative_file)
    monkeypatch.setattr(app.thumbnail.paths, 'get_candidates_folder',mock_get_candidates_folder)       
    monkeypatch.setattr(app.thumbnail.paths, 'get_video_file_url',mock_get_video_file_url)       
    monkeypatch.setattr(app.thumbnail.views, 'call_ffmpeg',mock_call_ffmpeg)       
    monkeypatch.setattr(random, 'randint',mock_randint)       

    # init
    print('\n\n\n--> Start test_get_candidates()')
    candidates_dir = paths.get_candidates_folder('some uid')
    global mock_randint_value
    mock_randint_value = 5
   
    print('--> --> test dir = {0}'.format(test_dir_path))
    print('--> --> candidates dir = {0}'.format(candidates_dir))

    # test algorithm
    print('--> --> Test URL route: get(/thumbnail/candidates/unit_11')
   
    # call test method by it's URL route with dummy unit id
    rv = client.get('/thumbnail/candidates/unit_11')

    # parse response and match expected response against actual response 
    #print('--> --> rv.status_code={0}   rv.data={1}'.format(rv.status_code, rv.data))   #.decode('UTF-8')
    test_pass = True
    if rv.status_code != 600:
        print('\nTest Error !!  expected return code={0}  is not equal to actual return code={1}  Message={2}'.format(600, rv.status_code, rv.data))
        test_pass = False
    else:    
        candidates_resp = json.loads(rv.data)
        candidate_records = candidates_resp['candidates']
        candidates_count = len(candidate_records)
        print('\nrecieved {0} candidates records:\n-------------------------\n'.format(candidates_count))
        
        mock_randint_value = 5
        for candidate_record in candidate_records:
            print('candidate_file={0}  url={1}'.format(candidate_record['candidate'], candidate_record['url']))
            expected_url = os.path.join(candidates_dir, 'c_' + str(mock_randint_value) + '.jpg')
            print('expected_url={0}'.format(expected_url))
            if expected_url != candidate_record['url']:
                print('\nTest Error !!  expected_url={0}  is not equal to actual url={1}'.format(expected_url, candidate_record['url']))
                test_pass = False
            mock_randint_value = mock_randint_value + 1
        #print('--> recieved data:{0}'.format(rv.data.decode('UTF-8')))
        
        if candidates_count != 10:
            test_pass = False
            print('\nTest Error !!  candidates_count={0}  should be 10'.format(candidates_count))

    clear_test()

    assert test_pass

def test_duplicated_candidates_due_to_same_time(client, monkeypatch):
    """test_duplicated_candidates_due_to_same_time"""
    
    def mock_randint(low, high):
        print('\n--> mock_randint() low={0}  high={1}  randint_return_value={2}'.format(low, high, 7))
        return 7    

    monkeypatch.setattr(app.thumbnail.paths, 'get_representative_file',mock_get_representative_file)
    monkeypatch.setattr(app.thumbnail.paths, 'get_candidates_folder',mock_get_candidates_folder)       
    monkeypatch.setattr(app.thumbnail.paths, 'get_video_file_url',mock_get_video_file_url)       
    monkeypatch.setattr(app.thumbnail.views, 'call_ffmpeg',mock_call_ffmpeg)       
    monkeypatch.setattr(random, 'randint',mock_randint)       

    # init
    print('\n\n\n--> Start test_duplicated_candidates_due_to_same_time()')
    candidates_dir = paths.get_candidates_folder('some uid')
    global mock_randint_value
    mock_randint_value = 5
   
    print('--> --> test dir = {0}'.format(test_dir_path))
    print('--> --> candidates dir = {0}'.format(candidates_dir))

    # test algorithm
    print('--> --> Test URL route: get(/thumbnail/candidates/unit_11')
   
    # call test method by it's URL route with dummy unit id
    rv = client.get('/thumbnail/candidates/unit_11')

    # parse response and match expected response against actual response 
    test_pass = True
    if rv.status_code != 600:
        print('\nTest Error !!  expected return code={0}  is not equal to actual return code={1}  Message={2}'.format(600, rv.status_code, rv.data))
        test_pass = False
    else:
        candidates_resp = json.loads(rv.data)
        candidate_records = candidates_resp['candidates']
        candidates_count = len(candidate_records)
        print('\nrecieved {0} candidates records:\n-------------------------\n'.format(candidates_count))
        
        # match expected response against actual response 
        test_pass = True
        mock_randint_value = 7
        for candidate_record in candidate_records:
            print('candidate_file={0}  url={1}'.format(candidate_record['candidate'], candidate_record['url']))
            expected_url = os.path.join(candidates_dir, 'c_' + str(mock_randint_value) + '.jpg')
            print('expected_url={0}'.format(expected_url))
            if expected_url != candidate_record['url']:
                print('\nTest Error !!  expected_url={0}  is not equal to actual url={1}'.format(expected_url, candidate_record['url']))
                test_pass = False
        
        if candidates_count != 10:
            test_pass = False
            print('\nTest Error !!  candidates_count={0}  should be 10'.format(candidates_count))

    clear_test()

    assert test_pass
    
def test_error_code_io_error(client, monkeypatch):
    """test_error_code_io_error"""
    
    def mock_call_ffmpeg(ffmpeg_bin, thumbnail_time, url, thumbnail_file):
        print('\n--> mock_call_ffmpeg() thumbnail_time={0}, url={1}, thumb_file={2}'.format(thumbnail_time, url, thumbnail_file))
        with open(thumbnail_file, 'w') as f:
            f.write('jpg_dummy_file={0}'.format(thumbnail_file))
        raise IOError()
        return 0   

    monkeypatch.setattr(app.thumbnail.paths, 'get_representative_file',mock_get_representative_file)
    monkeypatch.setattr(app.thumbnail.paths, 'get_candidates_folder',mock_get_candidates_folder)       
    monkeypatch.setattr(app.thumbnail.paths, 'get_video_file_url',mock_get_video_file_url)       
    monkeypatch.setattr(app.thumbnail.views, 'call_ffmpeg',mock_call_ffmpeg)       
    monkeypatch.setattr(random, 'randint',mock_randint)       

    # init
    print('\n\n\n--> Start test_error_code_io_error()')
    candidates_dir = paths.get_candidates_folder('some uid')
    global mock_randint_value
    mock_randint_value = 5
   
    print('--> --> test dir = {0}'.format(test_dir_path))
    print('--> --> candidates dir = {0}'.format(candidates_dir))

    # test algorithm
    print('--> --> Test URL route: get(/thumbnail/candidates/unit_11')
   
    # call test method by it's URL route with dummy unit id
    rv = client.get('/thumbnail/candidates/unit_11')

    # parse response and match expected response against actual response 
    test_pass = True
    if rv.status_code != 601:
        print('\nTest Error !!  expected return code={0}  is not equal to actual return code={1}'.format(601, rv.status_code))
        test_pass = False
    
    clear_test()

    assert test_pass

def test_error_code_video_not_found(client, monkeypatch):
    """test_error_code_video_not_found"""
    
    def mock_get_representative_file(unit_id):
        print('\n--> mock_get_representative_file() unit_id={0}'.format(unit_id))
        return [None, 55]   

    monkeypatch.setattr(app.thumbnail.paths, 'get_representative_file',mock_get_representative_file)
    monkeypatch.setattr(app.thumbnail.paths, 'get_candidates_folder',mock_get_candidates_folder)       
    monkeypatch.setattr(app.thumbnail.paths, 'get_video_file_url',mock_get_video_file_url)       
    monkeypatch.setattr(app.thumbnail.views, 'call_ffmpeg',mock_call_ffmpeg)       
    monkeypatch.setattr(random, 'randint',mock_randint)       

    # init
    print('\n\n\n--> Start test_error_code_video_not_found()')
    candidates_dir = paths.get_candidates_folder('some uid')
    global mock_randint_value
    mock_randint_value = 5
   
    print('--> --> test dir = {0}'.format(test_dir_path))
    print('--> --> creating candidates dir = {0}'.format(candidates_dir))
    os.makedirs(candidates_dir, exist_ok=True)
    # test algorithm
    print('--> --> Test URL route: get(/thumbnail/candidates/unit_11')
   
    # call test method by it's URL route with dummy unit id
    rv = client.get('/thumbnail/candidates/unit_11')

    # parse response and match expected response against actual response 
    test_pass = True
    if rv.status_code != 601:
        print('\nTest Error !!  expected return code={0}  is not equal to actual return code={1}'.format(601, rv.status_code))
        test_pass = False
    
    if os.path.isdir(candidates_dir):
        print('\nTest Error !!  expected that candidates dir={0} will be deleted but it exists'.format(candidates_dir))
        test_pass = False

    clear_test()

    assert test_pass

def clear_test():
    print ('\n--> Start clear test')
    views.delete_candidate_dir('dummy')

