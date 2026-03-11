# RAG Identifiers

## document_key
- Prefer: `source_system:business_id`
- Fallback: `source_system:normalized_path`

## version_fingerprint
SHA256 over:
- file_hash
- file_size
- modified timestamp
- text_hash

## Qdrant point id
`{version_id}:{chunk_index:04d}`

## Retrieval default
Always filter on:
- `is_latest = true`
- `is_active = true`
