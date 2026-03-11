# RAG Ingestion Operations

## latest-active rule
All production retrieval must filter on `is_latest=true` and `is_active=true`.

## version_fingerprint rule
Same `document_key` + same `version_fingerprint` means skip.
Same `document_key` + different `version_fingerprint` means create a new version and supersede the old one.

## dense + sparse ingestion
Each chunk may carry:
- dense vector
- sparse vector
- version-aware payload metadata

For Qdrant hybrid retrieval, dense and sparse representations should be written during ingestion so retriever queries can reuse the same version-governed chunk records.

## qdrant hybrid collections
Qdrant collections should be configured with:
- named dense vectors
- named sparse vectors
- payload indexes for document/version/status fields

## hybrid retrieval path
Retriever keeps the same external contract, but backend retrieval may use Qdrant dense search + sparse search + fusion / hybrid query primitives internally.

## encoder boundaries
- query encoders produce dense+sparse query forms
- document encoders produce dense+sparse chunk vectors for ingestion
- FastEmbed should live in the adapter layer, not in retriever core business logic

## live search path
A live Qdrant backend should:
- build named dense query args
- build named sparse query args
- apply latest-active filters
- normalize hits back into retriever candidates

## runtime + smoke path
A runtime-backed smoke path should prove:
- query runtime -> `RuntimeQueryEncoder`
- document runtime -> `RuntimeDocumentEncoder`
- chunk encoding -> hybrid ingest preparation
- version-aware ingest -> retriever backend -> tool output

This smoke path is useful for validating architecture wiring before depending on a real FastEmbed/Qdrant environment in production.

## nightly cleanup
Run daily during off-peak hours. Delete Qdrant points for superseded inactive versions older than retention.

## reconciliation
Regularly compare DB active chunk counts against Qdrant active point counts.
