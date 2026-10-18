"""Owner-scoped, aggregate-only classification reliability triage.

Operations feedback is not external ground truth; this is an audit/triage report.
"""
from collections import Counter
from .feedback_quality import active_feedback, CATEGORIES
from .models import DocumentClassification


def reliability_report(documents):
    active=list(active_feedback(documents))
    counts=Counter()
    for decision in active:
        current=DocumentClassification.objects.filter(document_id=decision.document_id).values_list('category',flat=True).first()
        if current is None:
            counts['missing_machine_prediction']+=1
        if current != decision.machine_category:
            counts['prediction_changed_since_review']+=1
        if decision.machine_category != decision.category:
            counts['review_disagreements']+=1
        if decision.machine_category == 'unknown' and decision.category != 'unknown':
            counts['owner_resolved_unknown']+=1
        if decision.machine_category != 'unknown' and decision.category == 'unknown':
            counts['owner_marked_unknown']+=1
    return {
        'basis':'owner_operational_feedback_not_independent_ground_truth',
        'reviewed_document_count':len(active),
        'triage_counts':{key:counts[key] for key in ('review_disagreements','prediction_changed_since_review','missing_machine_prediction','owner_resolved_unknown','owner_marked_unknown')},
        'priority_order':['missing_machine_prediction','prediction_changed_since_review','review_disagreements','owner_marked_unknown','owner_resolved_unknown'],
        'warning':'Operational owner feedback does not establish classifier accuracy. Independently adjudicated evaluation runs offline.'
    }
