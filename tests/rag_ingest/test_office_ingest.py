import os
import shutil
import tempfile
import zipfile

from rag_ingest.file_ingest import scan_files, read_text_file


def _write_minimal_docx(path):
    with zipfile.ZipFile(path, 'w') as zf:
        zf.writestr('[Content_Types].xml', '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"></Types>')
        zf.writestr('word/document.xml', '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>文件編號: SOP-003</w:t></w:r></w:p><w:p><w:r><w:t>DOCX ingest works</w:t></w:r></w:p></w:body></w:document>')


def _write_minimal_pptx(path):
    with zipfile.ZipFile(path, 'w') as zf:
        zf.writestr('[Content_Types].xml', '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"></Types>')
        zf.writestr('ppt/slides/slide1.xml', '<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><p:cSld><p:spTree><p:sp><p:txBody><a:p><a:r><a:t>文件編號: SOP-004</a:t></a:r></a:p><a:p><a:r><a:t>PPTX ingest works</a:t></a:r></a:p></p:txBody></p:sp></p:spTree></p:cSld></p:sld>')


def test_scan_files_includes_docx_and_pptx():
    root = tempfile.mkdtemp(prefix='rag_office_')
    try:
        _write_minimal_docx(os.path.join(root, 'doc.docx'))
        _write_minimal_pptx(os.path.join(root, 'deck.pptx'))
        names = sorted([os.path.basename(x) for x in scan_files(root)])
        assert 'doc.docx' in names
        assert 'deck.pptx' in names
    finally:
        shutil.rmtree(root)


def test_read_text_file_extracts_text_from_docx():
    root = tempfile.mkdtemp(prefix='rag_office_')
    try:
        path = os.path.join(root, 'doc.docx')
        _write_minimal_docx(path)
        text = read_text_file(path)
        assert 'SOP-003' in text
        assert 'DOCX ingest works' in text
    finally:
        shutil.rmtree(root)


def test_read_text_file_extracts_text_from_pptx():
    root = tempfile.mkdtemp(prefix='rag_office_')
    try:
        path = os.path.join(root, 'deck.pptx')
        _write_minimal_pptx(path)
        text = read_text_file(path)
        assert 'SOP-004' in text
        assert 'PPTX ingest works' in text
    finally:
        shutil.rmtree(root)
