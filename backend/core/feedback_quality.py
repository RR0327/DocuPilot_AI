"""Privacy-conserving operational feedback analysis; NEVER a model accuracy estimate.

Only the latest active owner decision per document enters comparisons. An override
is a human opinion, not independently adjudicated truth.
"""
from collections import Counter
from uuid import uuid4
from django.db.models import Prefetch
from .models import ClassificationFeedback, DocumentClassification

CATEGORIES = tuple(DocumentClassification.Category.values)


def active_feedback(documents):
    """Return effective latest decisions for a scoped Document QuerySet."""
    decisions = (ClassificationFeedback.objects.filter(document__in=documents)
                 .select_related('document')
                 .order_by('document_id', '-created_at', '-id'))
    seen = set()
    for item in decisions.iterator():
        if item.document_id in seen:
            continue
        seen.add(item.document_id)
        if item.action != 'clear':
            yield item


def analyze_feedback(documents):
    counts = Counter()
    matrix = {machine: {human: 0 for human in CATEGORIES} for machine in CATEGORIES}
    machine_changed_since_decision = 0
    for item in active_feedback(documents):
        counts['reviewed'] += 1
        # Compare against machine prediction AT REVIEW TIME, not mutable current classification.
        machine, human = item.machine_category, item.category
        if machine not in matrix or human not in matrix[machine]:
            counts['invalid_label_pairs'] += 1
            continue
        matrix[machine][human] += 1
        counts['agreement' if machine == human else 'disagreement'] += 1
        current = DocumentClassification.objects.filter(document_id=item.document_id).values_list('category',flat=True).first()
        if current != machine:
            machine_changed_since_decision += 1
    eligible = counts['agreement'] + counts['disagreement']
    total = documents.count()
    return {
        'basis': 'operational_owner_feedback_not_independent_ground_truth',
        'privacy': 'aggregate_only',
        'document_count': total,
        'reviewed_document_count': counts['reviewed'],
        'unreviewed_document_count': max(total - counts['reviewed'], 0),
        'agreement_count': counts['agreement'],
        'disagreement_count': counts['disagreement'],
        'agreement_rate': round(counts['agreement']/eligible,4) if eligible else None,
        'coverage_rate': round(counts['reviewed']/total,4) if total else None,
        'machine_changed_since_decision_count': machine_changed_since_decision,
        'invalid_label_pair_count': counts['invalid_label_pairs'],
        'labels': list(CATEGORIES),
        'confusion_matrix': matrix,
        'warning': 'Agreement is not accuracy; reviews are operational opinions, not independent labels.'
    }


def make_private_label_export(documents):
    """Pseudonymous, label-only snapshot; omits source content and identifiers.

    IDs are random for each export, preventing a persistent linkage key. Never
    use this export as an independent text classification benchmark.
    """
    rows = []
    for entry in active_feedback(documents):
        if entry.category not in CATEGORIES or entry.machine_category not in CATEGORIES:
            continue
        rows.append({
            'sample_id': str(uuid4()),
            'machine_label_at_review': entry.machine_category,
            'human_label': entry.category,
            'review_action': entry.action,
        })
    return {
        'dataset_type': 'pseudonymous_operational_feedback_labels_only',
        'independent_ground_truth': False,
        'includes_original_document_text': False,
        'sample_count': len(rows),
        'cases': rows,
        'limitations': 'No text/pages; not usable with the document classifier benchmark. Human decisions are not independent adjudication.'
    }
