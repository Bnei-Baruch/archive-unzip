import re
import difflib
import urllib

from flask import Blueprint, current_app, request
from flask.helpers import make_response
import webvtt

from app.doc2html.conversionFunctions import docx_to_text
from app.doc2html.views import process_docx_uid

# endpoint of mapping of timecode for CU transcription from .vtt file
# by language and CU uid
blueprint = Blueprint('time_code', __name__)

vtt_q = """
SELECT f.uid from files f 
INNER JOIN content_units cu ON cu.id = f.content_unit_id
WHERE cu.uid = '%s' 
AND f.properties->>'insert_type' = 'subtitles'
AND f.language = '%s'
"""
file_q = """
        select f.* from files f
        INNER JOIN content_units cu ON cu.id = f.content_unit_id
        WHERE cu.uid = '%s'
        AND f.language = '%s'
        """


@blueprint.route('/time_code')
def timecode():
    lang = request.args.get('language')
    cu_uid = request.args.get('uid')
    if lang is None or cu_uid is None:
        return {}
    p = TimecodeToDoc(cu_uid, lang)
    return p.run()


def text_by_file(f_uid):
    [docx_path], [code] = process_docx_uid([f_uid])
    if not docx_path or code != 200:
        return make_response('Failed preparing uid: [%s].' % docx_path, code)
    text = docx_to_text(docx_path)
    return clear_str(text).split(" ")


class TimecodeToDoc:
    def __init__(self, cu_uid, lang):
        self.resp = {}
        self.cu_uid = cu_uid
        self.lang = lang
        self.time_by_word_sub = {}
        self.time_by_word_doc = {}
        self.duration = 0

    def run(self):
        from_subs = self.prepare_subs()
        if from_subs is None:
            return {}
        from_doc = self.prepare_transcription()
        resp = {}
        try:
            resp = self.calculate_resp(from_subs, from_doc)
        except Exception as e:
            current_app.logger.error('Calculate times for unit %s. Exception %s' % (self.cu_uid, e))
        return resp

    def find_start_end_by_idxs(self, i1, i2):
        try:
            if i2 == len(self.time_by_word_sub):
                i2 = i1
            if i2 not in self.time_by_word_sub:
                i1 = i1 - 1
                i2 = i2 - 1
            start = self.time_by_word_sub[i1]
            end = self.time_by_word_sub[i2 + 1]
            return start, end
        except Exception as e:
            current_app.logger.error(e)

    # TRANSCRIPTIONS
    def prepare_transcription(self):
        try:
            fuid = self.file_by_cu()
            text = text_by_file(fuid)
        except Exception as e:
            return make_response(e, 500)
        return text

    def file_by_cu(self):
        q = file_q % (self.cu_uid, self.lang)
        with current_app.mdb.get_cursor() as cur:
            cur.execute(q)
            rows = cur.fetchall()
            for d in rows:
                if not d:
                    continue
                if d['type'] == "text":
                    uid = d['uid']
                if d['type'] == "video" and self.duration == 0:
                    self.duration = d['properties']['duration']
            return uid

    # SUBS
    def prepare_subs(self):
        with current_app.mdb.get_cursor() as cur:
            q = vtt_q % (self.cu_uid, self.lang)
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
            offset, t = self.approximate_sub_time(sub, offset)
            t_list += t
        return t_list

    def approximate_sub_time(self, sub, w_offset):
        t = clear_str(sub.text)
        s = sub.start_in_seconds * 1000
        e = sub.end_in_seconds * 1000
        t_list = t.split(" ")
        coef = (e - s) / len(t_list)

        w_count = 0
        for w in t_list:
            self.time_by_word_sub[w_offset + w_count] = s + w_count * coef
            w_count += 1
        return w_offset + w_count, t_list

    def calculate_resp(self, from_subs, from_doc):
        d = difflib.SequenceMatcher(lambda x: x in " ")
        d.set_seqs(from_subs, from_doc)
        diff = d.get_opcodes()
        resp = {}
        i = 0
        l = len(diff)
        while i < l:
            _last = i == (l - 1)
            (tag, i1, i2, j1, j2) = diff[i]
            try:
                if _last:
                    t_start = self.time_by_word_sub[i1 - 1]
                    t_end = self.duration
                else:
                    t_start, t_end = self.find_start_end_by_idxs(i1, i2)
            except Exception as e:
                current_app.logger.error(e)
            if tag == 'equal' or tag == 'replace':
                for (pos, t) in approximate_doc_time(j1, j2, t_start, t_end):
                    resp[pos] = RespItem(t, pos)
            # for insert we can pake time or from prev delete or from next delete if have
            elif tag == 'insert':
                try:
                    p_tag, p_i1, p_i2, p_j1, p_j2 = diff[i - 1]
                    n_tag, n_i1, n_i2, n_j1, n_j2 = diff[i + 1]
                    if p_tag == 'delete':
                        t_start = self.time_by_word_sub[p_i1]
                        t_end = self.time_by_word_sub[i2]
                    elif n_tag == 'delete':
                        if i + 2 < l and diff[i + 2][0] == "insert":
                            i += 1
                            continue
                        t_start = self.time_by_word_sub[i1]
                        t_end = self.time_by_word_sub[n_i2]
                    elif i1 == i2:
                        t_start = self.time_by_word_sub[p_i2]
                        t_end = self.time_by_word_sub[i2]
                    else:
                        t_start = self.time_by_word_sub[i1]
                        t_end = self.time_by_word_sub[i2]

                    for (pos, t) in approximate_doc_time(j1, j2, t_start, t_end):
                        resp[pos] = RespItem(t, pos)
                except Exception as e:
                    current_app.logger.error('Calculate response for iteration num %s. Exception %s' % (i, e))
            i += 1
        return resp


class RespItem(dict):
    def __init__(self, t, idx):
        dict.__init__(self, timeCode=t, index=idx)


def approximate_doc_time(j1, j2, s_time, e_time):
    try:
        w_len = j2 - j1
        coef = 0 if w_len == 0 else (e_time - s_time) / w_len

        resp = []
        t_offset = s_time
        w_count = 0
        while w_count < w_len:
            resp.append((j1 + w_count, round((t_offset + w_count * coef) / 1000, 1)))
            w_count += 1
        return resp
    except Exception as e:
        current_app.logger.error(e)


# must be synchronized with client side clean text cause we use letter position for find timestamp
# function findOffsetOfDOMNode
# https://github.com/Bnei-Baruch/kmedia-mdb/blob/263c76a7d7c790d1f4863f75a5aee97f820e04c4/src/helpers/scrollToSearch/helper.js#L243
pattern = re.compile(r'[".,\/#!$%\^&\*;:{}=\-_`~()\[\]‘’”“]')


def clear_str(text):
    text = re.sub(pattern, '', text)
    return re.sub(r'\W+', ' ', text)
