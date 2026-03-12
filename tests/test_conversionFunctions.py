import os
import subprocess
import tempfile
from unittest.mock import patch, MagicMock

import pytest

from app.doc2html.conversionFunctions import pdf_to_text, html_to_text, is_gibberish
from app.doc2html.views import is_single_uid, _safe_join


# ---------------------------------------------------------------------------
# is_single_uid — path traversal security boundary
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("uid", [
    "abc123",
    "U3d812xj",
    "A",
    "z",
    "000000",
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789",
])
def test_is_single_uid_accepts_valid_uids(uid):
    assert is_single_uid(uid), f"Expected valid UID to be accepted: {uid!r}"


@pytest.mark.parametrize("uid", [
    # Path traversal attempts
    "../../etc/passwd",
    "../secret",
    "..%2F..%2Fetc%2Fpasswd",
    "abc/../../etc/shadow",
    "/etc/passwd",
    # Null bytes
    "abc\x00def",
    # Special characters
    "abc def",
    "abc.def",
    "abc-def",
    "abc_def",
    "abc!def",
    "abc@def",
    # Empty string
    "",
    # Comma-separated (many UIDs, not single)
    "abc123,def456",
])
def test_is_single_uid_rejects_path_traversal_and_invalid_input(uid):
    assert not is_single_uid(uid), f"Expected invalid/dangerous UID to be rejected: {uid!r}"


# ---------------------------------------------------------------------------
# pdf_to_text — bug: returncode not checked
# ---------------------------------------------------------------------------

def test_pdf_to_text_returns_empty_when_pdftotext_fails_with_stdout():
    """Bug: pdf_to_text does not check result.returncode.

    When pdftotext exits non-zero but writes something to stdout (e.g. a
    partial error message or garbled output), the function currently returns
    that content as if it were valid extracted text.

    After the fix, any non-zero returncode must produce an empty string.
    """
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
        tmp_path = f.name
    try:
        with patch('app.doc2html.conversionFunctions.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout=b'Syntax Error (34): Expected the xref keyword.',
                stderr=b'pdftotext: Syntax Error',
            )
            result = pdf_to_text(tmp_path)
        assert result == '', (
            f'Expected empty string on pdftotext failure (returncode=1), '
            f'got: {result!r}'
        )
    finally:
        os.unlink(tmp_path)


def test_pdf_to_text_returns_text_on_success():
    """Sanity: valid pdftotext output is returned as-is."""
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
        tmp_path = f.name
    try:
        with patch('app.doc2html.conversionFunctions.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='Hello world'.encode('utf-8'),
                stderr=b'',
            )
            result = pdf_to_text(tmp_path)
        assert result == 'Hello world'
    finally:
        os.unlink(tmp_path)


def test_pdf_to_text_returns_empty_when_stdout_is_empty():
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
        tmp_path = f.name
    try:
        with patch('app.doc2html.conversionFunctions.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=b'',
                stderr=b'',
            )
            result = pdf_to_text(tmp_path)
        assert result == ''
    finally:
        os.unlink(tmp_path)


def test_pdf_to_text_returns_empty_when_pdftotext_not_found():
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
        tmp_path = f.name
    try:
        with patch('app.doc2html.conversionFunctions.subprocess.run',
                   side_effect=FileNotFoundError):
            result = pdf_to_text(tmp_path)
        assert result == ''
    finally:
        os.unlink(tmp_path)


def test_pdf_to_text_returns_empty_on_timeout():
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
        tmp_path = f.name
    try:
        with patch('app.doc2html.conversionFunctions.subprocess.run',
                   side_effect=subprocess.TimeoutExpired(cmd='pdftotext', timeout=60)):
            result = pdf_to_text(tmp_path)
        assert result == ''
    finally:
        os.unlink(tmp_path)


# ---------------------------------------------------------------------------
# html_to_text
# ---------------------------------------------------------------------------

def test_html_to_text_extracts_paragraph_text():
    with tempfile.NamedTemporaryFile(suffix='.html', delete=False,
                                     mode='w', encoding='utf-8') as f:
        f.write('<html><body><p>Hello</p><p>World</p></body></html>')
        tmp_path = f.name
    try:
        result = html_to_text(tmp_path)
        assert 'Hello' in result
        assert 'World' in result
    finally:
        os.unlink(tmp_path)


def test_html_to_text_skips_scripts_and_styles():
    with tempfile.NamedTemporaryFile(suffix='.html', delete=False,
                                     mode='w', encoding='utf-8') as f:
        f.write('<html><body>'
                '<script>var x=1;</script>'
                '<style>.foo{color:red}</style>'
                '<p>Visible</p>'
                '</body></html>')
        tmp_path = f.name
    try:
        result = html_to_text(tmp_path)
        assert 'var x' not in result
        assert '.foo' not in result
        assert 'Visible' in result
    finally:
        os.unlink(tmp_path)


def test_html_to_text_returns_empty_on_missing_file():
    result = html_to_text('/nonexistent/path/file.html')
    assert result == ''


# ---------------------------------------------------------------------------
# is_gibberish
# ---------------------------------------------------------------------------

def test_is_gibberish_clean_english():
    assert is_gibberish('This is a normal English sentence.') is False


def test_is_gibberish_hebrew_text():
    assert is_gibberish('שלום עולם, זהו טקסט עברי רגיל.') is False


def test_is_gibberish_corrupted_text():
    assert is_gibberish('łØœæłØœæłØœæ normal text') is True


def test_is_gibberish_empty_string():
    assert is_gibberish('') is True


def test_is_gibberish_none():
    assert is_gibberish(None) is True


def test_is_gibberish_short_text():
    assert is_gibberish('hi') is True  # < 10 chars


# ---------------------------------------------------------------------------
# _safe_join — path traversal prevention
# ---------------------------------------------------------------------------

def test_safe_join_normal_path():
    with tempfile.TemporaryDirectory() as base:
        result = _safe_join(base, 'U3', 'U3d812xj', 'U3d812xj.txt')
        assert result.startswith(base)


def test_safe_join_rejects_traversal_via_dotdot():
    with tempfile.TemporaryDirectory() as base:
        with pytest.raises(ValueError, match='Path traversal'):
            _safe_join(base, '..', 'etc', 'passwd')


def test_safe_join_rejects_absolute_escape():
    with tempfile.TemporaryDirectory() as base:
        with pytest.raises(ValueError, match='Path traversal'):
            _safe_join(base, '/etc/passwd')


def test_safe_join_rejects_encoded_traversal():
    with tempfile.TemporaryDirectory() as base:
        # os.path.realpath resolves these, so the confinement check catches them
        with pytest.raises(ValueError, match='Path traversal'):
            _safe_join(base, 'abc', '..', '..', '..', 'etc', 'passwd')


def test_safe_join_allows_nested_subdirectory():
    with tempfile.TemporaryDirectory() as base:
        result = _safe_join(base, 'doc2html', 'U3', 'U3d812xj')
        assert result == os.path.realpath(os.path.join(base, 'doc2html', 'U3', 'U3d812xj'))
