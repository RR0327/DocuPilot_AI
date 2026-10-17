"""Owner-scoped SQLite-friendly lexical retrieval and extractive answers.

No embeddings, external models or invented answers. Scores rank evidence; they are
not calibrated probabilities. Only exact source excerpts are returned as answers.
"""
import re
from collections import Counter
from dataclasses import dataclass

from django.db import transaction

from .models import DocumentChunk

MAX_CHARS = 900
OVERLAP = 120
MAX_QUERY_LENGTH = 500
STOPWORDS = frozenset('a an the is are was were of for to in on and or at by with what which who when where how does do did please tell me show give from about this that these those my document documents invoice invoices amount information'.split())
WORD_RE = re.compile(r"[^\W_]+(?:[-'][^\W_]+)*", re.UNICODE)


def tokens(text):
    return [w.lower() for w in WORD_RE.findall(text) if len(w) > 1 and w.lower() not in STOPWORDS]


def split_text(text, max_chars=MAX_CHARS, overlap=OVERLAP):
    """Bounded character chunks; preserves exact spans and offsets for citation."""
    if max_chars < 2 or overlap < 0 or overlap >= max_chars:
        raise ValueError('Invalid chunk sizes')
    result = []
    cursor = 0
    while cursor < len(text):
        end = min(cursor + max_chars, len(text))
        if end < len(text):
            boundary = max(text.rfind('\n', cursor + max_chars // 2, end),
                           text.rfind(' ', cursor + max_chars // 2, end))
            if boundary > cursor:
                end = boundary + 1
        if end <= cursor:
            end = min(cursor + max_chars, len(text))
        fragment = text[cursor:end]
        if fragment.strip():
            result.append((cursor, end, fragment))
        if end == len(text):
            break
        cursor = max(cursor + 1, end - overlap)
    return result


def rebuild_document_chunks(document):
    """Call within the caller's extraction transaction after pages are stored."""
    document.chunks.all().delete()
    chunks = []
    for page in document.pages.order_by('page_number'):
        for index, (start, end, content) in enumerate(split_text(page.extracted_text)):
            chunks.append(DocumentChunk(document=document, page_number=page.page_number,
                                        chunk_index=index, start_offset=start, end_offset=end,
                                        content=content))
    DocumentChunk.objects.bulk_create(chunks, batch_size=200)
    return len(chunks)


@dataclass(frozen=True)
class Evidence:
    document_id: int
    document_title: str
    page_number: int
    excerpt: str
    chunk_id: int
    score: float


def retrieve(owner, query, document_ids=None, limit=5):
    terms = Counter(tokens(query))
    if not terms:
        return []
    qs = DocumentChunk.objects.filter(document__owner=owner, document__processing_status='completed').select_related('document')
    if document_ids is not None:
        qs = qs.filter(document_id__in=document_ids)
    # SQLite-supported ORM filtering (portable fallback; bounded by user scope).
    # Ranking requires token boundaries to avoid partial-word false matches.
    from django.db.models import Q
    match_filter = Q()
    for term in terms:
        match_filter |= Q(content__icontains=term)
    qs = qs.filter(match_filter).order_by('document_id', 'page_number', 'chunk_index')
    ranked = []
    for chunk in qs.iterator(chunk_size=200):
        content_tokens = Counter(tokens(chunk.content))
        score = sum(min(content_tokens[t], 3) * (1 + min(terms[t], 2) * 0.15)
                    for t in terms if content_tokens[t])
        if score <= 0:
            continue
        # Require at least one exact lexical match; document title alone cannot answer.
        ranked.append(Evidence(chunk.document_id, chunk.document.title,
                               chunk.page_number, chunk.content.strip(), chunk.pk,
                               round(float(score), 3)))
    ranked.sort(key=lambda hit: (-hit.score, hit.document_id, hit.page_number, hit.chunk_id))
    # Collapse overlapping windows from the same page to reduce repeated citations.
    selected = []
    seen_pages = set()
    for hit in ranked:
        key = (hit.document_id, hit.page_number)
        if key not in seen_pages:
            selected.append(hit)
            seen_pages.add(key)
        if len(selected) >= limit:
            break
    return selected


def answer_from_evidence(evidence):
    if not evidence:
        return 'Insufficient evidence found in your indexed documents.'
    # Direct quotation: do not paraphrase or claim unsupported inferences.
    return evidence[0].excerpt[:700]
