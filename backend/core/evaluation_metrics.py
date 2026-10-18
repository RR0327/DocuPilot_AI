"""Dependency-free evaluation measures. Scores are benchmark diagnostics, never confidence.

All strings remain local. CER compares Unicode code points (not grapheme clusters).
"""
from decimal import Decimal, InvalidOperation


def edit_distance(reference, candidate):
    """Levenshtein distance with O(min(n,m)) working memory."""
    if len(reference) < len(candidate):
        reference, candidate = candidate, reference
    previous = list(range(len(candidate) + 1))
    for i, source_char in enumerate(reference, 1):
        current = [i]
        for j, target_char in enumerate(candidate, 1):
            current.append(min(current[-1] + 1, previous[j] + 1,
                               previous[j-1] + (source_char != target_char)))
        previous = current
    return previous[-1]


def character_error_rate(reference, candidate):
    if not isinstance(reference, str) or not isinstance(candidate, str):
        raise TypeError('OCR reference and prediction must be strings')
    if not reference:
        return 0.0 if not candidate else 1.0
    return round(edit_distance(reference, candidate) / len(reference), 6)


def retrieval_metrics(cases):
    """cases: expected key (or None), ranked list of result keys, source_integrity.

    Source integrity must be checked against the original indexed page, not model output.
    An abstention means no retrieved evidence for an expected no-answer query.
    """
    answerable = [c for c in cases if c['expected'] is not None]
    unanswerable = [c for c in cases if c['expected'] is None]
    count = len(answerable)
    hits = sum(c['expected'] in c['ranked'][:5] for c in answerable)
    reciprocal = sum(1 / (c['ranked'].index(c['expected']) + 1)
                     for c in answerable if c['expected'] in c['ranked'])
    abstains = sum(not c['ranked'] for c in unanswerable)
    return {
        'answerable_count': count,
        'unanswerable_count': len(unanswerable),
        'recall_at_5': round(hits / count, 4) if count else None,
        'mrr': round(reciprocal / count, 4) if count else None,
        'no_evidence_abstention_rate': round(abstains / len(unanswerable), 4) if unanswerable else None,
        'citation_integrity_rate': round(sum(c['source_integrity'] for c in cases) / len(cases), 4) if cases else None,
    }


def invoice_field_accuracy(rows):
    """Strict exact matching of expected ground-truth fields incl. explicit nulls."""
    matched = total = 0
    for expected, predicted in rows:
        for key, truth in expected.items():
            total += 1
            if predicted.get(key) == truth:
                matched += 1
    return {'field_count': total, 'exact_matches': matched,
            'exact_match_rate': round(matched / total, 4) if total else None}


def check_source_excerpt(page_text, excerpt):
    """No normalization: citation must be an actual contiguous substring."""
    return isinstance(excerpt, str) and bool(excerpt) and excerpt in page_text
