import html
import os
import subprocess
import multiprocessing
from html.parser import HTMLParser

import pypandoc
import tidylib

from docx import Document

soffice_lock = multiprocessing.Lock()

tidy_options = {
    "clean": "yes",
    "drop-proprietary-attributes": "yes",
    "drop-empty-paras": "yes",
    "output-html": "yes",
    "input-encoding": "utf8",
    "output-encoding": "utf8",
    "join-classes": "yes",
    "join-styles": "yes",
    "show-body-only": "yes",
    "force-output": "yes"
}


# Timeouts for doc_to_docx. Larger files, i.e., >1Mb might take 10 seconds.
SOFFICE_OUTSIDE_LOCK_TIMEOUT = 60*15  # 15 minutes
SOFFICE_INSIDE_LOCK_TIMEOUT = 600     # 10 minutes.
SOFFICE_SETUP_TIME = 5                # 5 seconds.
SOFFICE_PER_FILE_TIMEOUT = 12         # 12 seconds.


# May have None in |doc_files|, order is important.
def doc_to_docx(folder, files, soffice_bin, logger):
    ret = [None]*len(files)
    not_none_files = [f for f in files if f is not None]
    for f in not_none_files:
        if not os.path.exists(os.path.join(folder, f)):
            return ret, 404, 'File not found: [%s]' % os.path.join(folder, f)
    cmd = '%s --headless --convert-to docx --outdir %s %s' % (
        soffice_bin, folder, ' '.join([os.path.join(folder, f)
                                       for f in not_none_files]))
    if not soffice_lock.acquire(block=True,
                                timeout=SOFFICE_OUTSIDE_LOCK_TIMEOUT):
        soffice_lock.release()
        return ret, 503, 'Timedout when trying to lock Soffice.'
    else:
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, shell=True)
        try:
            timeout = min(SOFFICE_INSIDE_LOCK_TIMEOUT,
                          max(SOFFICE_SETUP_TIME,
                              SOFFICE_PER_FILE_TIMEOUT*len(not_none_files)))
            stdout, stderr = p.communicate(timeout=timeout)
            success_uids = []
            fail_uids = []
            for idx, doc_path in enumerate(files):
                if doc_path is not None:
                    dest_docx = os.path.join(folder, doc_path + 'x')
                    if os.path.exists(dest_docx):
                        ret[idx] = dest_docx
                        success_uids.append(dest_docx)
                    else:
                        fail_uids.append(dest_docx)
                        ret[idx] = None
                else:
                    ret[idx] = None
            assert(len(not_none_files) ==
                   len(success_uids) + len(fail_uids))
            if len(not_none_files) and not len(success_uids):
                return ret, 503, 'Soffice failed did not convert anything.'
            return ret, 200, ''
        except subprocess.TimeoutExpired:
            logger.error('Soffice timeout for %s.' % cmd)
            return ret, 503, 'Soffice timeout.'
        finally:
            soffice_lock.release()


def docx_to_html(src, dest, logger):
    if not os.path.exists(src):
        raise IOError('File not found: [%s]' % src)
    pypandoc.convert_file(src, to='html5', extra_args=['-s'], outputfile=dest)

    with open(dest, 'r') as f:
        h = f.read().replace('\n', '')
        h = html.unescape(h)

    markup, err = tidylib.tidy_document(h, tidy_options)
    if err:
        logger.warning("Tidy Error: %s", err)

    with open(dest, 'w') as f:
        f.write(markup)

    return dest


def docx_to_text(src):
    ret = []
    with open(src, 'rb') as f:
        document = Document(f)
        first = True
        for p in document.paragraphs:
            if not first:
                ret.append('\n')
            ret.append(p.text)
            if first:
                first = False
    return ''.join(ret)
