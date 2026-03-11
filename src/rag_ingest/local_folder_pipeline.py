import hashlib

from rag_ingest.business_id_strategy import resolve_business_id
from rag_ingest.contracts import build_document_key, build_version_fingerprint
from rag_ingest.embedding_provider import select_embedding_provider
from rag_ingest.file_ingest import scan_files, normalize_path, read_text_file, chunk_text
from rag_ingest.services.ingest_pipeline import ingest_document


def process_folder_documents(root_dir, session, qdrant, source_system='localfs', chunk_size=400, overlap=50, embedding_provider=None):
    processed = 0
    provider = embedding_provider or select_embedding_provider()
    for path in scan_files(root_dir):
        text = read_text_file(path)
        id_resolution = resolve_business_id(text, path)
        business_id = id_resolution['business_id']
        document_key = build_document_key(source_system, business_id, normalize_path(path))
        file_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()
        version_fingerprint = build_version_fingerprint(file_hash, len(text), None, file_hash)
        chunks = chunk_text(text, chunk_size=chunk_size, overlap=overlap)
        vectors = provider.embed_texts(chunks)
        metadata = {
            'document_key': document_key,
            'version_fingerprint': version_fingerprint,
            'source_system': source_system,
            'business_id': business_id,
            'normalized_path': normalize_path(path),
            'title': path.split('/')[-1],
            'doc_type': path.split('.')[-1].lower(),
            'business_id_source': id_resolution['source'],
            'business_id_conflict': id_resolution['conflict'],
            'filename_candidate': id_resolution['filename_candidate'],
            'content_candidate': id_resolution['content_candidate'],
            'file_hash': file_hash,
            'text_hash': file_hash,
            'file_size': len(text),
            'embedding_model': provider.name,
            'embedding_version': 'v1',
        }
        ingest_document(session, qdrant, metadata, chunks, vectors)
        processed += 1
    return {'processed': processed}
