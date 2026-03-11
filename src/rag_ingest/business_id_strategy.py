import os
import re


ID_PATTERNS = [
    r'文件編號\s*[:：]\s*([A-Z]+-\d+)',
    r'表單編號\s*[:：]\s*([A-Z]+-\d+)',
    r'(SOP-\d+)',
    r'(DOC-\d+)',
    r'(WI-\d+)',
]


def extract_id_from_text(text):
    for pattern in ID_PATTERNS:
        m = re.search(pattern, text)
        if m:
            return m.group(1)
    return None


def extract_id_from_filename(filename):
    name = os.path.basename(filename)
    for pattern in ID_PATTERNS:
        m = re.search(pattern, name)
        if m:
            return m.group(1)
    return None


def resolve_business_id(content_text, filename):
    content_candidate = extract_id_from_text(content_text or '')
    filename_candidate = extract_id_from_filename(filename or '')

    conflict = False
    source = None
    business_id = None

    if content_candidate and filename_candidate:
        if content_candidate == filename_candidate:
            business_id = content_candidate
            source = 'content'
        else:
            business_id = content_candidate
            source = 'content'
            conflict = True
    elif content_candidate:
        business_id = content_candidate
        source = 'content'
    elif filename_candidate:
        business_id = filename_candidate
        source = 'filename'

    return {
        'business_id': business_id,
        'source': source,
        'filename_candidate': filename_candidate,
        'content_candidate': content_candidate,
        'conflict': conflict,
    }
