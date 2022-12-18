import io
import json
import os
from pathlib import Path
from urllib import request
from zipfile import ZipFile
from PIL import Image, ImageChops, ImageStat, ImageEnhance, ImageColor, ImageFilter

from flask import Blueprint, current_app, request as requestFlask, jsonify
from flask.helpers import make_response

MODULE_DIR = 'unzip'
INDEX_JSON = 'index.json'
INDEX_UNIQ_JSON = 'index_uniq.json'
MIN_SAME_IMG_COEFFICIENT = 0.6
MIN_DIFF_PXL_AMOUNT = 20 * 1000

blueprint = Blueprint('unzip', __name__)


@blueprint.route('/unzip/<uid>')
def unzip(uid):
    file_path, _ = process_uid(uid)
    if file_path:
        return current_app.sendfile.send_file(file_path)
    else:
        return make_response("missing info", 404)


@blueprint.route('/unzip_uids')
def unzip_uids():
    uids = requestFlask.args.getlist('uid')
    list = []
    for uid in uids:
        try:
            path, uniq_path = process_uid(uid, True)
        # if can't find by this uid - skip
        except Exception as e:
            current_app.logger.debug('Try fetch and build json for file uid %s. Error %s', uid, e)
            continue
        with open(path, 'r') as f:
            full = json.loads(f.read())
        with open(uniq_path, 'r') as f:
            uniq = json.loads(f.read())
        list.append({'full': full, 'uniq': uniq, 'uid': uid})
    return jsonify(list)

def process_uid(uid, mast_uniq=False):
    base_dir = current_app.config['BASE_DIR']
    output_dir = os.path.join(base_dir, MODULE_DIR)
    os.makedirs(output_dir, exist_ok=True)

    uid_dir = os.path.join(output_dir, uid)
    index_file = os.path.join(uid_dir, INDEX_JSON)
    index_uniq_file = os.path.join(uid_dir, INDEX_UNIQ_JSON)

    # file already exist ?
    if os.path.exists(index_file) and (not mast_uniq or os.path.exists(index_uniq_file)):
        return index_file, index_uniq_file
    # unzip url to directory
    # TODO: handle http errors and map them to relevant errors to our users
    if not os.path.exists(index_file):
        url = current_app.config['LINKER_URL'] + uid
        try:
            conn = request.urlopen(url)
        except Exception as e:
            raise e
        zipstream = io.BytesIO(conn.read())
        with ZipFile(zipstream) as zipfile:
            for info in zipfile.infolist():
                zipfile.extract(info, path=uid_dir)

    # list files in directory
    files = []
    for file in sorted(os.listdir(uid_dir)):
        if not file.startswith(".") and not file.endswith('.json'):
            path = os.path.join(uid_dir, file)
            files.append({'path': path, 'size': os.path.getsize(path)})
    full, uniq = mark_main_img(files)
    # dump full list to index json
    with open(index_file, 'w') as out:
        json.dump(full, out)
    # dump list of unique to index_uniq json
    with open(index_uniq_file, 'w') as out:
        json.dump(uniq, out)
    return index_file, index_uniq_file


def mark_main_img(files):
    full = []
    uniq = []
    for idx, f1 in enumerate(files, start=1):
        path = current_app.sendfile.public_path(f1['path'])
        full.append({'path': path, 'size': f1['size']})
        have_continue = idx < len(files) and is_have_continue(f1['path'], files[idx]['path'])
        # skip broken image
        if len(files) > idx > 1 and not have_continue:
            have_continue = is_have_continue(files[idx - 2]['path'], files[idx]['path'])
        if not have_continue:
            uniq.append({'path': path, 'size': f1['size']})
    return full, uniq


# First check if next img have big different of active pixels (black)
# if not check amount of crossed active pixels
def is_have_continue(f1, f2):
    if f1 is None or f2 is None:
        return True
    fn = lambda x: 255 if x > 200 else 0
    img1 = Image.open(f1).convert('L').point(fn, mode='1').convert('1').filter(ImageFilter.MedianFilter(3))
    img2 = Image.open(f2).convert('L').point(fn, mode='1').convert('1').filter(ImageFilter.MedianFilter(3))
    img1 = crop_border(img1)
    img2 = crop_border(img2)
    cross_img = ImageChops.add(img1, img2)
    img1_black = img1.getcolors()[0][0]
    img2_black = img2.getcolors()[0][0]
    min_b = min(img1_black, img2_black)
    cross_b = cross_img.getcolors()[0][0]
    has_continue = not (img1_black - img2_black > MIN_SAME_IMG_COEFFICIENT and img1_black / img2_black > 3) and \
                   (abs(min_b - cross_b) / min_b < MIN_SAME_IMG_COEFFICIENT)
    #save_for_debug(False, img1, img2, cross_img, f1)
    return has_continue


def crop_border(img):
    w, h = img.size
    bbox = img.getbbox()
    if not bbox == (0, 0, w, h):
        return img.crop(bbox)
    return img


def save_for_debug(skip, img1, img2, cross_img, f1):
    if skip:
        return
    diff_img = ImageChops.difference(img1, img2)
    num = f1.split(".")[0].split("_")[-1]
    Path("/assets/unzip/diff").mkdir(parents=True, exist_ok=True)
    img1.save("/assets/unzip/diff/{num}.jpg".format(num=num))
    img2.save("/assets/unzip/diff/{num}_next.jpg".format(num=num))
    cross_img.save("/assets/unzip/diff/{num}_cross.jpg".format(num=num))
    diff_img.save("/assets/unzip/diff/{num}_diff.jpg".format(num=num))
