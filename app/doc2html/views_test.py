from unittest.mock import Mock
from . import views
import urllib
import os

from app import app


mock_uids = {}


def mock_get_file_types(uids):
    return [mock_uids[uid].file_type for uid in uids]
views.get_file_types = Mock(side_effect=mock_get_file_types)


def mock_request(url, path):
    if not mock_uids[os.path.basename(url)].exist:
        raise 'Failed downloaind file.'
    open(path, 'a').close()
urllib.request = Mock(side_effect=mock_request)


app = app.create_app('test')


def test_is_single_uid():
    assert views.is_single_uid('uID12')
    assert not views.is_single_uid('uID12,23d3vG')


def test_is_single_or_many_uid():
    assert views.is_single_or_many_uid('abc123')
    assert views.is_single_or_many_uid('abc123,')
    assert views.is_single_or_many_uid('abc123,321qew')
    assert views.is_single_or_many_uid('abc123/321qew')


def test_process_docx_uid():
    with app.app_context():
        global file_types
        file_types.extend(['doc', 'docx', 'doc'])
        assert (views.process_docx_uid(['one', 'two', 'three']) ==
                ([1, 2, 3], [200, 200, 200]))
