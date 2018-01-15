import os
import subprocess

import pypandoc
import tidylib

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


def doc_to_docx(doc_file, soffice_bin, logger):
    if not os.path.exists(doc_file):
        raise IOError('File not found: [%s]' % doc_file)

    logger.debug("Start doc->docx convertion. Path: %s", doc_file)

    working_dir = os.path.dirname(doc_file)
    cmd = '%s --headless --convert-to docx --outdir %s %s' % (soffice_bin, working_dir, doc_file)
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    try:
        stdout, stderr = p.communicate(timeout=15)
    except TimeoutError:
        p.kill()
        raise
    else:
        logger.debug(stdout.decode(encoding='UTF-8'))
        if len(stderr) > 0:
            raise IOError(stderr)

    logger.debug("Done converting from doc to docx")

    return doc_file + 'x'


def docx_to_html(src, dest, logger):
    if not os.path.exists(src):
        raise IOError('File not found: [%s]' % src)

    logger.debug("Start docx->html conversion (pandoc) src: %s, dest: %s", src, dest)
    pypandoc.convert_file(src, to='html5', extra_args=['-s'], outputfile=dest)
    logger.debug("Done converting from docx to html (pandoc) src: %s, dest: %s", src, dest)

    logger.debug("Start to tidy html. Input file [%s]", dest)
    with open(dest, 'r') as f:
        html = f.read().replace('\n', '')

    markup, err = tidylib.tidy_document(html, tidy_options)
    if err:
        logger.warning("Tidy Error: %s", err)

    with open(dest, 'w') as f:
        f.write(markup)

    logger.info("Done tidy html file [%s]", dest)

    return dest
