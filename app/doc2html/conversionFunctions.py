import os
import subprocess
import multiprocessing
from html.parser import HTMLParser
from html import unescape

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
    pypandoc.convert_file(src, to='html5', extra_args=['--standalone', '--self-contained'], outputfile=dest)

    with open(dest, 'r') as f:
        html = f.read().replace('\n', '')

    markup, err = tidylib.tidy_document(html, tidy_options)
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


class HTMLTextExtractor(HTMLParser):
    """Extract text from HTML, preserving paragraph structure"""

    def __init__(self):
        super().__init__()
        self.text_parts = []
        self.current_text = []
        # Block-level elements that should trigger new lines
        self.block_tags = {
            'p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'li', 'tr', 'br', 'hr', 'blockquote', 'pre',
            'article', 'section', 'header', 'footer'
        }
        # Tags that contain content we want to skip
        self.ignore_tags = {'script', 'style'}
        self.ignore_depth = 0
        self.in_head = False

    def handle_starttag(self, tag, attrs):
        if tag == 'head':
            self.in_head = True
        elif tag in self.ignore_tags:
            self.ignore_depth += 1

    def handle_endtag(self, tag):
        if tag == 'head':
            self.in_head = False
        elif tag in self.ignore_tags:
            self.ignore_depth = max(0, self.ignore_depth - 1)
        elif tag in self.block_tags and self.current_text:
            # Flush current text as a paragraph
            text = ' '.join(self.current_text).strip()
            if text:
                self.text_parts.append(text)
            self.current_text = []

    def handle_data(self, data):
        if not self.in_head and self.ignore_depth == 0:
            text = data.strip()
            if text:
                self.current_text.append(text)

    def get_text(self):
        # Flush any remaining text
        if self.current_text:
            text = ' '.join(self.current_text).strip()
            if text:
                self.text_parts.append(text)
        return '\n'.join(self.text_parts)


def html_to_text(html_path):
    """Convert HTML file to plain text, one paragraph per line"""
    try:
        # Try to detect encoding from file content
        with open(html_path, 'rb') as f:
            raw_content = f.read()

        # Try common encodings in order
        encodings = ['utf-8', 'windows-1251', 'cp1251', 'iso-8859-1', 'latin1']
        html_content = None

        for encoding in encodings:
            try:
                html_content = raw_content.decode(encoding)
                # If it decoded successfully and has reasonable content, use it
                if html_content and len(html_content) > 100:
                    break
            except (UnicodeDecodeError, AttributeError):
                continue

        if not html_content:
            # Fallback to utf-8 with error handling
            html_content = raw_content.decode('utf-8', errors='replace')

        # Decode HTML entities
        html_content = unescape(html_content)

        # Extract text
        extractor = HTMLTextExtractor()
        extractor.feed(html_content)
        return extractor.get_text()
    except Exception as e:
        # Log and return empty string on error
        return ''


def is_gibberish(text, threshold=0.05, max_gibberish_chars=100):
    """Detect if text is likely gibberish from encoding issues

    Returns True if text appears to be corrupted/gibberish based on:
    - Ratio of unusual Unicode characters > 5%
    - OR absolute count of gibberish characters > 100

    Normal documents should have 0% gibberish characters.

    Args:
        text: Text to check
        threshold: Ratio of gibberish chars to total (0.05 = 5%)
        max_gibberish_chars: Max absolute count of gibberish chars (100)
    """
    if not text or len(text.strip()) < 10:
        return True

    # Characters commonly seen in Hebrew PDF encoding issues
    gibberish_chars = 'łØœæªÆºŁ↓ıĄĘŚŻÖÜäöü'

    gibberish_count = 0
    total_chars = 0

    for char in text:
        if char.strip():  # Count non-whitespace
            total_chars += 1
            if char in gibberish_chars:
                gibberish_count += 1

    if total_chars == 0:
        return True

    # Check both ratio AND absolute count
    ratio = gibberish_count / total_chars

    # Return True if EITHER condition is met
    if gibberish_count > max_gibberish_chars:
        return True  # Too many gibberish chars in absolute terms

    if ratio > threshold:
        return True  # Too high a percentage of gibberish

    return False


def ocr_pdf(pdf_path, logger=None, max_pages=10):
    """Extract text from PDF using OCR (slow fallback for problematic PDFs)

    Requires: tesseract-ocr, poppler-utils, pytesseract, pdf2image

    Args:
        pdf_path: Path to PDF file
        logger: Optional logger
        max_pages: Maximum pages to OCR (default 10, to avoid very long processing)

    Returns:
        Extracted text or empty string on failure
    """
    try:
        from pdf2image import convert_from_path
        import pytesseract

        # Convert PDF pages to images
        # Use lower DPI (200) for speed, limit to max_pages
        images = convert_from_path(
            pdf_path,
            dpi=200,  # Lower DPI = faster, 200 is usually sufficient
            first_page=1,
            last_page=max_pages
        )

        if not images:
            return ''

        # OCR each page with Hebrew, Russian, English support
        text_parts = []
        for i, image in enumerate(images):
            try:
                text = pytesseract.image_to_string(
                    image,
                    lang='heb+rus+eng',  # Multi-language support
                    config='--psm 6'  # Assume uniform block of text
                )
                if text.strip():
                    text_parts.append(text.strip())
            except Exception as e:
                if logger:
                    logger.warning(f'OCR failed for page {i+1} of {pdf_path}: {e}')
                continue

        result = '\n\n'.join(text_parts)

        if logger and result:
            logger.info(f'OCR extracted {len(result)} chars from {len(images)} pages of {pdf_path}')

        return result

    except ImportError as e:
        if logger:
            logger.error(f'OCR dependencies not installed: {e}')
        return ''
    except Exception as e:
        if logger:
            logger.error(f'OCR failed for {pdf_path}: {e}')
        return ''


def pdf_to_text(pdf_path, logger=None):
    """Convert PDF to text using pdftotext command

    Note: Some Hebrew PDFs may have encoding issues that cannot be fixed by pdftotext.
    This is a limitation of the PDF format and the embedded fonts/encoding.
    """
    try:
        # Try without encoding flag first (use PDF's native encoding)
        result = subprocess.run(
            ['pdftotext', '-layout', pdf_path, '-'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=60
        )

        # Retry with explicit UTF-8 if failed (non-zero exit) or produced no output
        if result.returncode != 0 or not result.stdout or not result.stdout.strip():
            result = subprocess.run(
                ['pdftotext', '-layout', '-enc', 'UTF-8', pdf_path, '-'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=60
            )

        if result.returncode != 0 or not result.stdout:
            return ''

        # Try to decode the output with various encodings — UTF-8 first
        try:
            text = result.stdout.decode('utf-8')
            if text.strip():
                return text
        except UnicodeDecodeError:
            pass

        # Try Hebrew encodings
        for encoding in ['cp1255', 'iso-8859-8', 'windows-1255', 'iso-8859-8-i']:
            try:
                text = result.stdout.decode(encoding)
                if text.strip():
                    return text
            except (UnicodeDecodeError, AttributeError):
                continue

        # Try Latin encodings as fallback
        for encoding in ['latin1', 'cp1252']:
            try:
                text = result.stdout.decode(encoding)
                if text.strip():
                    return text
            except (UnicodeDecodeError, AttributeError):
                continue

        # Last resort: replace undecodable bytes rather than failing completely
        return result.stdout.decode('utf-8', errors='replace')

    except subprocess.TimeoutExpired:
        if logger:
            logger.error(f'pdftotext timeout for {pdf_path}')
        return ''
    except FileNotFoundError:
        if logger:
            logger.warning('pdftotext not found, PDF extraction unavailable')
        return ''
