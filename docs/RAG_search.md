# Retrieval-Augmented Generation (RAG) – Search Pipeline

This document explains, in reader-friendly terms, how ATLAS Darwin performs **Retrieval-Augmented Generation (RAG)** search across the Darwin Correspondence corpus using hybrid search architecture.  Developer-level details are provided in call-outs.

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

1. **Hybrid search** combines dense vector search (HNSW) with sparse BM25 lexical search to capture both semantic similarity and exact term matches across Darwin's correspondence.
2. **Reciprocal Rank Fusion** merges and re-ranks results from both search methods, balancing semantic understanding with lexical precision.
3. The **LLM** receives the top-K passages plus running chat-memory to generate answers with rich Darwin metadata and scholarly citations.

---

## 2 Hybrid Search Architecture

**Dense Vector Component:**
* **Backend:** [`langchain_community.vectorstores.Chroma`] with HNSW indexing
* **Model:** `Livingwithmachines/bert_1760_1900` (historical text optimized)
* **Pooling:** `mean+max` strategy for optimal performance
* **Chunks:** 1,200-character sliding window (`chunk_size = 1200`, `chunk_overlap = 200`)

**Sparse Lexical Component:**
* **Algorithm:** BM25 (Best Matching 25) for exact term matching
* **Purpose:** Captures precise terminology, names, and phrases that embeddings might miss
* **Storage:** Pre-computed BM25 corpus saved as `bm25_corpus.jsonl`

**Metadata Enhancement:**
* **TEI Entities:** Person names, places, organizations, and taxonomic terms
* **Darwin Project URLs:** Canonical scholarly citations with permanent identifiers
* **Letter Metadata:** Dates, correspondents, archival locations

Vector-store creation is handled by `create/Darwin/xml/create_darwin_store.py`.  Each run emits a **manifest** (stats & config) under `create/Darwin/xml/output/darwin.txt` – this allows the retriever generator to stay in sync with the store.

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

| Variable | Purpose | Darwin Default |
|----------|---------|----------------|
| `LARGE_RETRIEVAL_SIZE_SINGLE_CORPUS` | Vector candidates fetched | **120** |
| `LARGE_RETRIEVAL_SIZE_ALL_CORPUS` | N/A (Darwin is single corpus) | **80** |
| `SEARCH_K` | Final top-K after RRF fusion | **20** (via target config) |

Change these in `.env.*` or the target config to trade recall vs. speed.

---

## 4 Darwin Correspondence Specifics

**Single Corpus Architecture:**
* Darwin ATLAS focuses on a single, unified corpus of ~15,000 letters
* No corpus filtering required—all searches span the complete correspondence
* Simplified retrieval pipeline optimized for historical letter structure

**Letter-Optimized Chunking:**
* Chunks respect Victorian letter conventions (salutations, body, signatures)
* Larger chunk size (1,200 chars) accommodates longer historical sentences
* Higher overlap (200 chars) ensures context preservation across chunk boundaries

---

## 5 Chat Memory & Stateless Retrieval

During a multi-turn conversation the frontend sends the running `chat_history` array.  The backend:

1. Serialises that history into the system prompt (last ~3 000 tokens; configurable).  
2. Does **not** change the vector search parameters—the same hybrid retrieval is executed every turn.  
3. May provide message-level memory to the LLM (provider-specific).

Because search is stateless, earlier turns do not bias result selection; only the **current** user question determines retrieval.

---

## 6 Hybrid Search Benefits

**Why Hybrid Search for Darwin?**

Darwin's correspondence presents unique challenges that hybrid search addresses:

| Challenge | Dense Vector Strength | BM25 Lexical Strength |
|-----------|----------------------|------------------------|
| Scientific terminology | Semantic relationships | Exact species names |
| Historical language | Contextual understanding | Period-specific terms |
| Person names | Name variations | Exact name matching |
| Geographic references | Related locations | Precise place names |
| Correspondence networks | Conceptual connections | Specific correspondent matching |

**RRF Fusion Advantages:**
* **Balanced results:** Neither search method dominates inappropriately
* **Complementary strengths:** Semantic similarity + lexical precision
* **Robust ranking:** Multiple ranking signals reduce single-point failures
* **Historical optimization:** Particularly effective for 19th-century correspondence

The final ranked list ensures scholars get both conceptually related passages and exact terminological matches.

---

## 7 Telemetry & Diagnostics

All retrieval spans emit OpenTelemetry attributes:

* `search_type`, `search_k`, `large_retrieval_size`, `pooling`, `corpus_filter`, etc.  
* Hybrid search metrics: `vector_results_count`, `bm25_results_count`, `rrf_fusion_score`

Use **Phoenix** to monitor the balance between dense and sparse retrieval components.

---

## 8 Darwin Configuration Cheatsheet

| Setting | Location | Darwin Value |
|---------|----------|--------------|
| Vector store path | `.env` → `CHROMA_PERSIST_DIRECTORY` | `backend/targets/chroma_db` |
| Collection name | `.env` → `CHROMA_COLLECTION_NAME` | `darwin` |
| Embedding model | `.env` → `EMBEDDING_MODEL` | `Livingwithmachines/bert_1760_1900` |
| Pooling strategy | `.env` → `POOLING` | `mean+max` |
| Chunk size | `.env` → `CHUNK_SIZE` | `1200` |
| Chunk overlap | `.env` → `CHUNK_OVERLAP` | `200` |
| Vector candidates | `.env` → `LARGE_RETRIEVAL_SIZE_SINGLE_CORPUS` | `120` |
| Final top-K | `backend/targets/<target>.txt` → `SEARCH_K` | `20` |
| Darwin XML (full) | `.env` → `DARWIN_XML_FULL_PATH` | `../../../../darwin_sources_FULL/xml/letters` |
| Darwin XML (test) | `.env` → `DARWIN_XML_TEST_PATH` | `../../../../darwin_sources_TEST/xml/letters` |

**Build Commands:**
* `make vs-full` - Create full Darwin corpus vector store (~15,000 letters, ~65 min)
* `make vs-test` - Create test Darwin corpus vector store (~16 letters, ~4 min)
* `make r` - Generate corresponding retriever with hybrid search capabilities

---

**Key takeaway:** Darwin's hybrid search architecture balances semantic understanding with lexical precision, ensuring scholars find both conceptually related content and exact terminological matches across 15,000+ historical letters. The RRF fusion mechanism prevents either search method from dominating, creating optimal retrieval for 19th-century correspondence research.