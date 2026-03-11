import os
import shutil
import tempfile

from rag_ingest.file_ingest import scan_files, normalize_path, extract_business_id, read_text_file, chunk_text


def make_temp_tree(files):
    root = tempfile.mkdtemp(prefix='rag_ingest_')
    for rel_path, content in files.items():
        full = os.path.join(root, rel_path)
        parent = os.path.dirname(full)
        if not os.path.isdir(parent):
            os.makedirs(parent)
        with open(full, 'w') as f:
            f.write(content)
    return root


def test_scan_files_finds_supported_documents_only():
    root = make_temp_tree({
        'a.md': '# title',
        'b.txt': 'hello',
        'c.html': '<p>x</p>',
        'ignore.bin': 'zzz',
    })
    try:
        results = scan_files(root)
        names = sorted([os.path.basename(x) for x in results])
        assert names == ['a.md', 'b.txt', 'c.html']
    finally:
        shutil.rmtree(root)


def test_normalize_path_returns_stable_slash_path():
    assert normalize_path('\\data\\specs\\doc.txt') == '/data/specs/doc.txt'


def test_extract_business_id_prefers_explicit_pattern():
    text = '文件編號: SOP-001\n內容...'
    assert extract_business_id(text) == 'SOP-001'


def test_read_text_file_handles_markdown_and_html_text():
    root = make_temp_tree({'doc.html': '<html><body><h1>Hello</h1><p>World</p></body></html>'})
    try:
        content = read_text_file(os.path.join(root, 'doc.html'))
        assert 'Hello' in content
        assert 'World' in content
    finally:
        shutil.rmtree(root)


def test_chunk_text_splits_long_text_into_multiple_chunks():
    text = ' '.join(['token'] * 120)
    chunks = chunk_text(text, chunk_size=30, overlap=5)
    assert len(chunks) > 1
    assert all(len(c) > 0 for c in chunks)
