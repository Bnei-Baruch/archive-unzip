import shutil
from datetime import datetime, timedelta
import os
from functools import reduce
from os.path import isfile, join
from subprocess import call
from tempfile import TemporaryDirectory
from urllib.request import urlretrieve

from flask import current_app, send_file

KTAIM_NIVCHARIM_TYPE_ID = 46
LESSONS_SERIES_TYPE_ID = 39
FIND_KITVEIMAKOR_AOUDIO_LINKS_SQL = """
    SELECT f.uid as uid FROM files f
        WHERE f.content_unit_id IN (%s)
        AND f.language = '%s'
        AND f.type = 'audio'
        AND f.published = TRUE
        AND f.secure = 0
        ORDER BY ;
"""
LIKUTIM_ORIGINALS_BY_DATE_SQL = """
    SELECT lesson_cu.properties->>'film_date' as film_date, km_cu.id as km_id, km_cu.properties->>'duration' as km_d
        FROM content_units likut_cu
        INNER JOIN content_unit_derivations lesson_cud ON  lesson_cud.derived_id = likut_cu.id
        INNER JOIN content_units lesson_cu ON lesson_cu.id = lesson_cud.source_id
        INNER JOIN content_unit_derivations km_cud ON  km_cud.source_id = lesson_cud.source_id 
        INNER JOIN content_units km_cu ON km_cu.id = km_cud.derived_id
        WHERE likut_cu.uid = '%s'
        AND km_cu.type_id = 31
        AND lesson_cu.published = TRUE
        AND lesson_cu.secure = 0
        ORDER BY (lesson_cu.properties->>'film_date')::date;
"""
CHECK_IS_LAST_SQL = """
    SELECT (cu.properties->>'film_date')::date FROM files f 
        INNER JOIN content_units cu ON f.content_unit_id = cu.id
        WHERE cu.uid = '%s'
        AND f.language = '%s'
        ORDER BY (cu.properties->>'film_date')::date DESC
"""


def fetch_audios(links, tmp_dir):
    try:
        for (l, uid) in links:
            urlretrieve(l, "%s/%s.mp3" % (tmp_dir, uid))
    except Exception as e:
        current_app.logger.error(e)


class KmAudio:
    def __init__(self, uid, lang):
        self.is_ok = False
        self.dir = "%s/kitvei_makor/" % current_app.config['BASE_DIR']
        self.path = os.path.join(self.dir, "%s_%s.mp3" % (uid, lang))
        self.uid = uid
        self.lang = lang
        self.order = []

    def run(self):
        os.makedirs(self.dir, exist_ok=True)
        if os.path.isfile(self.path) and not self.need_update():
            return self.path
        with TemporaryDirectory() as tmp_dir:
            links = self.find_audios()
            fetch_audios(links, tmp_dir)
            if len(links) > 1:
                self.merge_audio(tmp_dir)
            else:
                self.cp_audio(tmp_dir)
        return self.is_ok

    def need_update(self):
        with current_app.mdb.get_cursor() as cur:
            cur.execute(CHECK_IS_LAST_SQL % (self.uid, self.lang))
            t = cur.fetchone()
            resp = t['date'] > (datetime.now() - timedelta(days=1)).date()
            return resp

    def find_audios(self):
        with current_app.mdb.get_cursor() as cur:
            cur.execute(LIKUTIM_ORIGINALS_BY_DATE_SQL % self.uid)
            rows = cur.fetchall()
            prev_dt = datetime(1990, 1, 1)
            duration = 0
            by_dt = []
            cu_ids = []
            for i, r in enumerate(rows):
                dt = datetime.strptime(r["film_date"], "%Y-%m-%d")
                cu_ids.append(r["km_id"])
                duration += int(r["km_d"])
                if dt - timedelta(days=10) < prev_dt or i == len(rows) - 1:
                    prev_dt = dt
                    x = {
                        "duration": duration,
                        "dt": dt,
                        "cu_ids": reduce(lambda a, b: "%s , %d" % (a, b), cu_ids)
                    }
                    by_dt.append(x)
            ids = max(by_dt, key=lambda item: item["duration"])

            cur.execute(FIND_KITVEIMAKOR_AOUDIO_LINKS_SQL % (ids["cu_ids"], self.lang))
            rows = cur.fetchall()
            link = []
            for r in rows:
                self.order.append(r["uid"])
                link.append(("%s%s.mp3" % (current_app.config['LINKER_URL'], r["uid"]), r["uid"]))
            return link

    def merge_audio(self, tmp_dir):
        ffmpeg_bin = current_app.config['FFMPEG_BIN']
        files = []
        for uid in self.order:
            p = join(tmp_dir, "%s.mp3" % uid)
            if not isfile(p):
                continue
            files.append("-i")
            files.append(p)
        ret_code = call([ffmpeg_bin, *files, "-c", "copy", self.path])
        self.is_ok = ret_code == 0

    def cp_audio(self, tmp_dir):
        for f in os.listdir(tmp_dir):
            p = join(tmp_dir, f)
            if not isfile(p):
                continue
            shutil.copyfile(p, self.path)
            self.is_ok = True
