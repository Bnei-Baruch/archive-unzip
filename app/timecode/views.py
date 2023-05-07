import os
import re
import difflib
import tempfile
import urllib
import time

from flask import Blueprint, current_app
from flask.helpers import make_response
import webvtt

from app.doc2html.conversionFunctions import docx_to_text
from app.doc2html.views import process_docx_uid

blueprint = Blueprint('time_code', __name__)

FIX_DERIVE_ZERO = 1 ** -10
time_by_word = {}
pos_by_word = {}
duration = 0

vtt_q = """
SELECT f.uid from files f 
INNER JOIN content_units cu ON cu.id = f.content_unit_id
WHERE cu.uid = '%s' 
AND f.properties->>'insert_type' = 'subtitles'
AND f.language = 'he'
"""


@blueprint.route('/time_code/<uid>')
def timecode(uid):
    global duration
    duration = 0
    from_subs = prepare_subs(uid)
    if from_subs is None:
        return {}
    from_doc = prepare_transcription(uid)
    resp = {}
    try:
        resp = calculate_resp(from_subs, from_doc)
    except Exception as e:
        current_app.logger.error('Calculate times for unit %s. Exception %s' % (uid, e))
    return resp


def calculate_resp(from_subs, from_doc):
    d = difflib.SequenceMatcher(lambda x: x in " \t")
    d.set_seqs(from_subs, from_doc)
    diff = d.get_opcodes()
    resp = {}
    i = 0
    l = len(diff)
    while i < l:
        _last = i == (l - 1)
        (tag, i1, i2, j1, j2) = diff[i]
        if _last:
            t_start = time_by_word[i2 - 1][1]
            global duration
            t_end = duration
        else:
            t_start, t_end = find_start_end_by_idxs(i1, i2)
        if tag == 'equal' or tag == 'replace':
            for (pos, time) in approximate_doc_time(j1, j2, t_start, t_end):
                resp[pos] = RespItem(time, pos)
        elif tag == 'insert':
            p2_tag = diff[i - 2][0]
            p_tag, p_i1, p_i2, p_j1, p_j2 = diff[i - 1]
            if p_tag == 'delete':
                if not p2_tag == "insert":
                    t_start, _ = time_by_word[p_i1]
                else:
                    _, t_start = time_by_word[p_i2]
            if not _last:
                n_tag, n_i1, n_i2, n_j1, n_j2 = diff[i + 1]
                if n_tag == 'delete':
                    _, t_end = time_by_word[n_i2]
                else:
                    t_end, _ = time_by_word[n_i1]
            for (pos, time) in approximate_doc_time(j1, j2, t_start, t_end):
                resp[pos] = RespItem(time, pos)
        i += 1
    return resp


class RespItem(dict):
    def __init__(self, t, idx):
        dict.__init__(self, timeCode=t, index=idx)


def approximate_doc_time(i1, i2, s_time, e_time):
    if i2 == len(pos_by_word):
        i2 = i1

    s_pos = pos_by_word[i1][0]
    e_pos = pos_by_word[i2][1]

    coef = (e_time - s_time) / (e_pos - s_pos + FIX_DERIVE_ZERO)

    resp = []
    t_offset = s_time
    while i1 <= i2:
        (s_pos, e_pos) = pos_by_word[i1]
        resp.append((s_pos, round(t_offset / 1000, 1)))
        t_offset = t_offset + (e_pos - s_pos + 1) * coef
        i1 += 1
    return resp


def find_start_end_by_idxs(i1, i2):
    if i2 == len(time_by_word):
        i2 = i1;
    if i2 not in time_by_word:
        i1 = i1 - 1
        i2 = i2 - 1
    start = time_by_word[i1][0]
    end = time_by_word[i2][1]
    return start, end


# TRANSCRIPTIONS
def prepare_transcription(uid):
    try:
        fuid = file_by_cu(uid)
        text = text_by_file(fuid)
        resp = save_pos_by_word(text)
    except Exception as e:
        return make_response(e, 500)
    return resp


def file_by_cu(uid):
    with current_app.mdb.get_cursor() as cur:
        q = "select f.* from files f " \
            "INNER JOIN content_units cu ON cu.id = f.content_unit_id " \
            "WHERE cu.uid = '%s'" % uid
        cur.execute(q)
        rows = cur.fetchall()
        global duration
        for d in rows:
            if not d:
                continue
            if d['type'] == "text":
                uid = d['uid']
            if d['type'] == "video" and duration == 0:
                duration = d['properties']['duration']
        return uid


def text_by_file(uid):
    [docx_path], [code] = process_docx_uid([uid])
    if not docx_path or code != 200:
        return make_response('Failed preparing uid: [%s].' % docx_path, code)
    text = docx_to_text(docx_path)
    return clear_str(text)


def save_pos_by_word(text):
    arr = text.split(' ')
    offset = 0
    i = 0
    for w in arr:
        pos_by_word[i] = (offset, offset + len(w))
        offset = offset + len(w) + 1
        i += 1
    return arr


# SUBS
def prepare_subs(uid):
    with current_app.mdb.get_cursor() as cur:
        q = vtt_q % uid
        cur.execute(q)
        f_uid = cur.fetchone()
    if f_uid is None:
        return None
    url = current_app.config['LINKER_URL'] + f_uid['uid']
    tmp, headers = urllib.request.urlretrieve(url)
    subs = webvtt.read(tmp)
    offset = 0
    t_list = []
    for sub in subs:
        offset, t = approximate_sub_time(sub, offset)
        t_list += t
    return t_list


def approximate_sub_time(sub, w_offset):
    t = clear_str(sub.text)
    s = str_2_mls(sub.start)
    e = str_2_mls(sub.end)
    coef = (e - s) / len(t)

    t_offset = s
    t_list = t.split(" ")
    for w in t_list:
        t_offset_end = t_offset + (len(w) + 1) * coef
        time_by_word[w_offset] = (t_offset, t_offset_end)
        w_offset += 1
        t_offset = t_offset_end
    return w_offset, t_list


# must be synchronized with client side clean text cause we use letter position for find timestamp
def clear_str(text):
    pattern = re.compile(r'[".,\/#!$%\^&\*;:{}=\-_`~()\[\]‘’”“]')
    text = re.sub(pattern, '', text)
    return re.sub(r'\W+', ' ', text)


def debug_diff_results(from_subs, from_doc, as_html):
    if not as_html:
        d = difflib.Differ()
        result = d.compare(from_subs, from_doc)
        for r in result:
            print("%s" % r)
        return

    if as_html:
        d = difflib.HtmlDiff()
        table = d.make_table(from_subs, from_doc)
        return table


def str_2_mls(st):
    _l = st.split('.')
    mls = int(_l[1])
    t = _l[0].split(':')
    i = len(t) - 1
    for s in t:
        mls += int(s) * max(i * 60, 1) * 1000
        i -= 1
    return mls
