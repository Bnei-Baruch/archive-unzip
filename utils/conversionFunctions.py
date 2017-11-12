#!/usr/bin/python3
# https://github.com/Bnei-Baruch/source-conversion/blob/master/sourcesToHtmlConversion/conversionFunctions.py

import json
import os
import subprocess

# pip3 install pypandoc && brew install pandoc
import pypandoc
# pip3 install pytidylib
import tidylib

# Warning: symlinks don't work, see https://superuser.com/a/1089693
soffice_bin = os.environ.get('API_SOFFICE_BIN', '/Applications/LibreOffice.app/Contents/MacOS/soffice')

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


def convert_from_doc_to_docx(working_dir, filename):
    doc_file = os.path.join(working_dir, filename + '.doc')
    if not os.path.exists(doc_file):
        raise IOError('File not found: [%s]' % doc_file)

    print("Start doc->docx convertion. Path: %s" % doc_file)

    cmd = '%s --headless --convert-to docx --outdir %s %s' % (soffice_bin, working_dir, doc_file)
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    stdout, stderr = p.communicate()
    print(stdout.decode(encoding='UTF-8'))
    if len(stderr) > 0:
        raise IOError(stderr)

    docx_file = doc_file + 'x'
    print("Done converting from doc to docx. File: %s" % docx_file)
    return docx_file


def convert_from_docx_to_html(uid):
    sourcepath = uid + '.docx'
    destpath = uid + '.html'

    print("Start docx->html convertion (pandoc) sourcepath: %s, destpath:%s" % (sourcepath, destpath))
    pypandoc.convert_file(sourcepath, to='html5', extra_args=['-s'], outputfile=destpath)
    print("Done converting from docx to html (pandoc) sourcepath:%s, destpath: %s" % (sourcepath, destpath))

    print("Start to tidy html. Input file '{}'".format(destpath))
    with open(destpath, 'r') as outfile:
        html_file_content = outfile.read().replace('\n', '')

    markup, errors = tidylib.tidy_document(html_file_content, tidy_options)
    if len(errors) > 0:
        print(errors)

    with open(destpath, 'w') as outfile:
        outfile.write(markup)

    print("Done tidy html file [%s]" % destpath)

    return destpath
