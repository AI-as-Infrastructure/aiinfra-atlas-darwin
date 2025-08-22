# Retrieval-Augmented Generation (RAG) – Search Pipeline

This document explains, in reader-friendly terms, how ATLAS performs **Retrieval-Augmented Generation (RAG)** search across historical document corpora using hybrid search architecture. Developer-level details are provided in call-outs.

## 1 Pipeline Overview

```text
┌─ User query ─┐
│              ▼
│  1. Hybrid Search: Dense vectors (HNSW) + BM25 lexical search
│              ▼
│  2. Reciprocal Rank Fusion (RRF)  →  Top-K passages  
│              ▼
└► 3. LLM context builder (chat memory + citations) ─► Answer
```

1. **Hybrid search** combines dense vector search (HNSW) with sparse BM25 lexical search to capture both semantic similarity and exact term matches across historical documents.
2. **Reciprocal Rank Fusion** merges and re-ranks results from both search methods, balancing semantic understanding with lexical precision.
3. The **LLM** receives the top-K passages plus running chat-memory to generate answers with rich document metadata and scholarly citations.

---

## 2 Hybrid Search Architecture

**Dense Vector Component:**
* **Backend:** [`langchain_community.vectorstores.Chroma`] with HNSW indexing
* **Model:** Configurable embedding model (optimized for domain-specific text)
* **Pooling:** Configurable pooling strategy for optimal performance
* **Chunks:** Configurable character sliding window (`chunk_size` and `chunk_overlap`)

**Sparse Lexical Component:**
* **Algorithm:** BM25 (Best Matching 25) for exact term matching
* **Purpose:** Captures precise terminology, names, and phrases that embeddings might miss
* **Storage:** Pre-computed BM25 corpus saved as `bm25_corpus.jsonl`

**Metadata Enhancement:**
* **Document Entities:** Person names, places, organizations, and domain-specific terms
* **Canonical URLs:** Scholarly citations with permanent identifiers (when available)
* **Document Metadata:** Dates, authors, archival locations, and corpus-specific fields

Vector-store creation is handled by corpus-specific creation scripts. Each run emits a **manifest** (stats & config) that allows the retriever generator to stay in sync with the store.

---

## 3 Reciprocal Rank Fusion (RRF)

The hybrid search combines results from both dense vector and BM25 searches using Reciprocal Rank Fusion:

```python
# Get candidates from both search methods
vector_results = vector_store.similarity_search(query, k=vector_k)
bm25_results = bm25.get_relevant_documents(query, k=bm25_k)

# Apply RRF scoring: score = 1/(rank + k_constant)
rrf_scores = reciprocal_rank_fusion([vector_results, bm25_results], k=60)
```

**RRF Parameters:**
* **k_constant:** 60 (standard value balancing rank position importance)
* **Fusion weight:** Equal weighting between dense and sparse results
* **Result merging:** Combines unique documents, summing RRF scores for duplicates

Environment variables:

| Variable | Purpose | Default |
|----------|---------|----------------|
| `LARGE_RETRIEVAL_SIZE_SINGLE_CORPUS` | Vector candidates fetched (single corpus) | **120** |
| `LARGE_RETRIEVAL_SIZE_ALL_CORPUS` | Vector candidates fetched (multi-corpus) | **80** |
| `SEARCH_K` | Final top-K after RRF fusion | **20** (via target config) |

Change these in `.env.*` or the target config to trade recall vs. speed.

---

## 4 Corpus Architecture

**Single vs. Multi-Corpus Support:**
* ATLAS supports both single corpus and multi-corpus configurations
* Corpus filtering available when multiple document collections are indexed
* Retrieval pipeline adapts to corpus structure and document types

**Document-Optimized Chunking:**
* Chunks respect document structure (sections, paragraphs, natural boundaries)
* Configurable chunk size accommodates document characteristics
* Overlap ensures context preservation across chunk boundaries

---

## 5 Chat Memory & Stateless Retrieval

During a multi-turn conversation the frontend sends the running `chat_history` array.  The backend:

1. Serialises that history into the system prompt (last ~3 000 tokens; configurable).  
2. Does **not** change the vector search parameters—the same hybrid retrieval is executed every turn.  
3. May provide message-level memory to the LLM (provider-specific).

Because search is stateless, earlier turns do not bias result selection; only the **current** user question determines retrieval.

---

## 6 Hybrid Search Benefits

**Why Hybrid Search for Historical Documents?**

Historical document collections present unique challenges that hybrid search addresses:

| Challenge | Dense Vector Strength | BM25 Lexical Strength |
|-----------|----------------------|------------------------|
| Domain terminology | Semantic relationships | Exact technical terms |
| Historical language | Contextual understanding | Period-specific vocabulary |
| Person names | Name variations | Exact name matching |
| Geographic references | Related locations | Precise place names |
| Document networks | Conceptual connections | Specific entity matching |

**RRF Fusion Advantages:**
* **Balanced results:** Neither search method dominates inappropriately
* **Complementary strengths:** Semantic similarity + lexical precision
* **Robust ranking:** Multiple ranking signals reduce single-point failures
* **Domain optimization:** Particularly effective for specialized historical collections

The final ranked list ensures researchers get both conceptually related passages and exact terminological matches.

---

## 7 Telemetry & Diagnostics

All retrieval spans emit OpenTelemetry attributes:

* `search_type`, `search_k`, `large_retrieval_size`, `pooling`, `corpus_filter`, etc.  
* Hybrid search metrics: `vector_results_count`, `bm25_results_count`, `rrf_fusion_score`

Use **Phoenix** to monitor the balance between dense and sparse retrieval components.

---

## 8 Configuration Reference

| Setting | Location | Purpose |
|---------|----------|----------|
| Vector store path | `.env` → `CHROMA_PERSIST_DIRECTORY` | Chroma database location |
| Collection name | `.env` → `CHROMA_COLLECTION_NAME` | Vector collection identifier |
| Embedding model | `.env` → `EMBEDDING_MODEL` | HuggingFace model for embeddings |
| Pooling strategy | `.env` → `POOLING` | Embedding pooling method |
| Chunk size | `.env` → `CHUNK_SIZE` | Document chunk size (characters) |
| Chunk overlap | `.env` → `CHUNK_OVERLAP` | Overlap between chunks (characters) |
| Vector candidates | `.env` → `LARGE_RETRIEVAL_SIZE_SINGLE_CORPUS` | Pre-fusion candidate count |
| Final top-K | `backend/targets/<target>.txt` → `SEARCH_K` | Final result count |

**Build Commands:**
* `make vs-full` - Create full corpus vector store
* `make vs-test` - Create test corpus vector store
* `make r` - Generate corresponding retriever with hybrid search capabilities

---

**Key takeaway:** ATLAS hybrid search architecture balances semantic understanding with lexical precision, ensuring researchers find both conceptually related content and exact terminological matches across historical document collections. The RRF fusion mechanism prevents either search method from dominating, creating optimal retrieval for specialized research domains.