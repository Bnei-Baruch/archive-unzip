import os
import re
import tempfile

import docx
import requests
from flask import Blueprint, request, current_app
from flask.helpers import make_response
from flask.json import jsonify

from app.doc2html.views import MODULE_DIR

countwordsBlueprint = Blueprint('countwords', __name__)


@countwordsBlueprint.route('/countwords', methods=["GET"])
def countwords():
    f_uid = request.args.get('f', type=str)
    if f_uid is None:
        return make_response("You must send files", 400)
    result = []
    doc = docx.Document(current_app.fetchfile.fetch_doc(f_uid, get_dir))
    for p in doc.paragraphs:
        w_map = countWords(p)
        if len(w_map) == 0:
            continue
        result.append(w_map)

    return make_response(jsonify(result), 200)

def get_dir(uid):
    return current_app.fetchfile.get_dir(uid, MODULE_DIR)

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
