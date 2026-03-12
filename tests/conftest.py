"""
Mock third-party and Flask dependencies so conversion function tests
can run without the full Docker environment.
"""
import sys
from unittest.mock import MagicMock

# Flask and its extensions
for _mod in ['flask', 'flask.helpers', 'flask_cors']:
    sys.modules.setdefault(_mod, MagicMock())

# Heavy doc-conversion libs used by other functions in conversionFunctions.py
# (not needed by the functions under test)
for _mod in ['pypandoc', 'tidylib', 'docx']:
    sys.modules.setdefault(_mod, MagicMock())

# Make `from docx import Document` work
sys.modules['docx'].Document = MagicMock()
