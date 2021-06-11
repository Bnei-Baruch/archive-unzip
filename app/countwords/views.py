import os
import re
import tempfile

import docx
import requests
from flask import Blueprint, request, current_app
from flask.helpers import make_response
from flask.json import jsonify

countwordsBlueprint = Blueprint('countwords', __name__)


@countwordsBlueprint.route('/countwords', methods=["GET"])
def countwords():
    f_uid = request.args.get('f', type=str)
    if f_uid is None:
        return make_response("You must send files", 400)
    result = []
    with tempfile.TemporaryDirectory() as tmp_dir:
        doc = fetchFile(f_uid, tmp_dir)
        for p in doc.paragraphs:
            w_map = countWords(p)
            if len(w_map) == 0:
                continue
            result.append(w_map)

    return make_response(jsonify(result), 200)


def fetchFile(uid, temp_dir):
    url = current_app.config['LINKER_URL'] + uid
    r = requests.get(url, allow_redirects=True)
    name = r.url.split('/')[-1]
    out_path = os.path.join(temp_dir, name)
    with open(out_path, 'wb') as f:
        f.write(r.content)
    return docx.Document(out_path)


def countWords(paragraph):
    t = re.sub('<,()"".*?>', '', paragraph.text)
    dic = dict()
    if t == "":
        return dic
    words = t.split()
    for w in words:
        if w == ',':
            continue
        if w not in dic:
            dic[w] = 0
        dic[w] = dic[w] + 1
    return dic
