import os
import re
import subprocess
import zipfile
from html.parser import HTMLParser
import xml.etree.ElementTree as ET

SUPPORTED_EXTENSIONS = ('.txt', '.md', '.html', '.htm', '.pdf', '.docx', '.pptx')


class _HTMLTextExtractor(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.parts = []

    def handle_data(self, data):
        if data and data.strip():
            self.parts.append(data.strip())

    def get_text(self):
        return ' '.join(self.parts)


def scan_files(root_dir):
    matches = []
    for current_root, _, files in os.walk(root_dir):
        for name in files:
            if name.lower().endswith(SUPPORTED_EXTENSIONS):
                matches.append(os.path.join(current_root, name))
    return sorted(matches)


def normalize_path(path):
    path = path.replace('\\', '/')
    if not path.startswith('/'):
        path = '/' + path.lstrip('/')
    return re.sub(r'/+', '/', path)


def extract_business_id(text):
    patterns = [
        r'文件編號\s*[:：]\s*([A-Z]+-\d+)',
        r'(SOP-\d+)',
        r'(DOC-\d+)',
    ]
    for pattern in patterns:
        m = re.search(pattern, text)
        if m:
            return m.group(1)
    return None


def _extract_xml_text(xml_bytes):
    root = ET.fromstring(xml_bytes)
    texts = []
    for elem in root.iter():
        if elem.text and elem.text.strip():
            texts.append(elem.text.strip())
    return ' '.join(texts)


def _read_docx(path):
    with zipfile.ZipFile(path, 'r') as zf:
        return _extract_xml_text(zf.read('word/document.xml'))


def _read_pptx(path):
    texts = []
    with zipfile.ZipFile(path, 'r') as zf:
        for name in sorted(zf.namelist()):
            if name.startswith('ppt/slides/slide') and name.endswith('.xml'):
                texts.append(_extract_xml_text(zf.read(name)))
    return ' '.join([t for t in texts if t])


def read_text_file(path):
    lower = path.lower()
    if lower.endswith('.pdf'):
        output = subprocess.check_output(['pdftotext', path, '-'], stderr=subprocess.STDOUT)
        return output.decode('utf-8', errors='ignore')
    if lower.endswith('.docx'):
        return _read_docx(path)
    if lower.endswith('.pptx'):
        return _read_pptx(path)
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    if lower.endswith('.html') or lower.endswith('.htm'):
        parser = _HTMLTextExtractor()
        parser.feed(content)
        return parser.get_text()
    return content


def chunk_text(text, chunk_size=400, overlap=50):
    tokens = text.split()
    if not tokens:
        return []
    if chunk_size <= 0:
        raise ValueError('chunk_size must be positive')
    if overlap < 0:
        raise ValueError('overlap must be >= 0')
    step = max(1, chunk_size - overlap)
    chunks = []
    start = 0
    while start < len(tokens):
        window = tokens[start:start + chunk_size]
        chunks.append(' '.join(window))
        start += step
    return chunks
