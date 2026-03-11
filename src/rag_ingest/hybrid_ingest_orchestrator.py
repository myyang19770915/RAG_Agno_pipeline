def prepare_hybrid_chunk_vectors(chunks, document_encoder):
    encoded_chunks = document_encoder.encode_chunks(chunks)
    dense_vectors = [chunk['dense'] for chunk in encoded_chunks]
    sparse_vectors = [chunk['sparse'] for chunk in encoded_chunks]
    return dense_vectors, sparse_vectors
