"""SQLite-compatible semantic and hybrid retrieval with optional local embeddings.

No external inference API. Text embeddings are cached in SQLite and invalidated
when a chunk is replaced. Scores express ranking, not evidential certainty.
"""
import math
from functools import lru_cache
from django.conf import settings
from django.db import transaction
from .models import DocumentChunk, ChunkEmbedding
from .search import Evidence, retrieve_keyword

MAX_SEMANTIC_CANDIDATES = 3000
MAX_TOP_K = 10


class SemanticUnavailable(RuntimeError):
    pass


@lru_cache(maxsize=1)
def _model():
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise SemanticUnavailable("Semantic model not installed. Run pip install -r backend/requirements-semantic.txt") from exc
    try:
        return SentenceTransformer(settings.DOCUPILOT_EMBEDDING_MODEL, local_files_only=settings.DOCUPILOT_MODEL_OFFLINE)
    except Exception as exc:
        raise SemanticUnavailable("Local embedding model unavailable. Download it once or select keyword mode.") from exc


def encode_texts(texts):
    """Injectable encoder for tests; returns normalized vectors."""
    model = _model()
    return [[float(x) for x in row] for row in model.encode(texts, normalize_embeddings=True, show_progress_bar=False)]


def cosine(a, b):
    if not a or len(a) != len(b):
        return 0.0
    a_norm = math.sqrt(sum(x*x for x in a))
    b_norm = math.sqrt(sum(x*x for x in b))
    if not a_norm or not b_norm:
        return 0.0
    return sum(x*y for x, y in zip(a, b)) / (a_norm*b_norm)


def retrieve_hybrid(owner, query, document_ids=None, limit=5, mode="hybrid"):
    if mode not in ("semantic", "hybrid"):
        raise ValueError("Unsupported retrieval mode")
    if not isinstance(limit, int) or not 1 <= limit <= MAX_TOP_K:
        raise ValueError("Invalid result limit")
    qs = DocumentChunk.objects.filter(document__owner=owner, document__processing_status="completed").select_related('document')
    if document_ids is not None:
        qs = qs.filter(document_id__in=document_ids)
    count = qs.count()
    if count > MAX_SEMANTIC_CANDIDATES:
        raise SemanticUnavailable("Too many indexed chunks for local semantic search; narrow your document selection.")
    chunks = list(qs.order_by('document_id', 'page_number', 'chunk_index'))
    if not chunks:
        return []
    model_id = settings.DOCUPILOT_EMBEDDING_MODEL
    cached = {row.chunk_id: row.vector for row in ChunkEmbedding.objects.filter(chunk_id__in=[c.id for c in chunks], model_name=model_id)}
    missing = [chunk for chunk in chunks if chunk.id not in cached]
    # Encode before caching, so an unavailable model causes no partial index writes.
    if missing:
        vectors = encode_texts(["passage: " + c.content for c in missing])
        if len(vectors) != len(missing):
            raise SemanticUnavailable('Unexpected embedding output size')
        with transaction.atomic():
            ChunkEmbedding.objects.bulk_create([ChunkEmbedding(chunk=chunk, model_name=model_id, vector=vector) for chunk, vector in zip(missing, vectors)], ignore_conflicts=True, batch_size=100)
        cached.update({chunk.id: vector for chunk, vector in zip(missing, vectors)})
    query_vector = encode_texts(["query: " + query])[0]
    # Semantic-only retrieval never turns a negative cosine score into evidence.
    scored = {}
    for chunk in chunks:
        similarity = cosine(query_vector, cached[chunk.id])
        if similarity >= settings.DOCUPILOT_SEMANTIC_MIN_SCORE:
            scored[chunk.id] = [chunk, similarity, 0]
    if mode == 'hybrid':
        # Reciprocal rank fusion combines lexical and semantic rankings while
        # avoiding incompatible raw-score units. Filtered after owner scoping.
        lexical = retrieve_keyword(owner, query, document_ids, limit=min(count, MAX_SEMANTIC_CANDIDATES))
        for rank, hit in enumerate(lexical, 1):
            if hit.chunk_id not in scored:
                chunk = next((c for c in chunks if c.id == hit.chunk_id), None)
                if chunk is not None:
                    scored[chunk.id] = [chunk, None, rank]
            else:
                scored[hit.chunk_id][2] = rank
    semantic_order = sorted([v for v in scored.values() if v[1] is not None], key=lambda v: (-v[1], v[0].id))
    semantic_ranks = {v[0].id: rank for rank, v in enumerate(semantic_order, 1)}
    ranked = []
    for chunk, sim, lexical_rank in scored.values():
        if mode == 'semantic':
            value = round(sim, 4)
        else:
            value = (1.0/(60 + semantic_ranks[chunk.id]) if chunk.id in semantic_ranks else 0) + (1.0/(60 + lexical_rank) if lexical_rank else 0)
            value = round(value, 6)
        ranked.append(Evidence(chunk.document_id, chunk.document.title, chunk.page_number, chunk.content.strip(), chunk.pk, value, mode))
    ranked.sort(key=lambda hit: (-hit.score, hit.document_id, hit.page_number, hit.chunk_id))
    selected, seen = [], set()
    for hit in ranked:
        key = (hit.document_id, hit.page_number)
        if key in seen:
            continue
        selected.append(hit)
        seen.add(key)
        if len(selected) >= limit:
            break
    return selected
