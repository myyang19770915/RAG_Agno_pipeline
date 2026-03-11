from rag_ingest.business_id_strategy import resolve_business_id


def test_uses_content_id_when_only_content_has_id():
    result = resolve_business_id(content_text='文件編號: SOP-001', filename='random_file.pdf')
    assert result['business_id'] == 'SOP-001'
    assert result['source'] == 'content'
    assert result['conflict'] is False


def test_uses_filename_id_when_content_missing():
    result = resolve_business_id(content_text='no id here', filename='SOP-002_作業標準.pdf')
    assert result['business_id'] == 'SOP-002'
    assert result['source'] == 'filename'
    assert result['conflict'] is False


def test_uses_id_when_content_and_filename_match():
    result = resolve_business_id(content_text='文件編號: SOP-003', filename='SOP-003_流程.docx')
    assert result['business_id'] == 'SOP-003'
    assert result['source'] == 'content'
    assert result['conflict'] is False


def test_marks_conflict_when_content_and_filename_differ():
    result = resolve_business_id(content_text='文件編號: SOP-004', filename='SOP-999_流程.docx')
    assert result['business_id'] == 'SOP-004'
    assert result['filename_candidate'] == 'SOP-999'
    assert result['content_candidate'] == 'SOP-004'
    assert result['conflict'] is True
