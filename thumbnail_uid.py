#!/usr/bin/python3

import os
from subprocess import call
from urllib import request

from flask.helpers import make_response

app_dir = 'thumbnail/'


def thumbnail_uid(uid, linker_base_url, base_dir):
    uid_dir = os.path.join(base_dir,app_dir, uid)
    os.makedirs(uid_dir, exist_ok=True)
    call(["ffmpeg", '-y',
          "-i", linker_base_url + uid + ".mp4",
          "-vf", "thumbnail=12",
          "-vframes", "1",
          "-vcodec", "png",
          uid_dir + "/" + uid + ".png"])

    return base_dir + "/" + app_dir + uid + ".mp4"





