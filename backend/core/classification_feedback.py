"""Owner-scoped human labels, with immutable machine decisions and append-only history."""
from django.db import transaction
from rest_framework.exceptions import ValidationError
from .models import ClassificationFeedback, DocumentClassification, ProcessingJob

CATEGORIES = {item.value for item in DocumentClassification.Category}
ACTIONS = {"verify", "override", "clear"}


def latest_decision(document):
    return document.classification_feedback.select_related("reviewer").order_by("-created_at", "-id").first()


def feedback_payload(document):
    prediction = DocumentClassification.objects.filter(document=document).first()
    decision = latest_decision(document)
    machine = prediction.category if prediction else None
    human = decision.category if decision and decision.action != "clear" else None
    return {
        "document_id": document.pk, "machine_category": machine,
        "verified_category": human, "effective_category": human if human is not None else machine,
        "review_status": "unreviewed" if not decision or decision.action == "clear" else "verified",
        "source_evidence": prediction.evidence if prediction else [],
        "history": [{"id": entry.pk, "action": entry.action, "category": entry.category or None,
                     "machine_category": entry.machine_category, "reviewer_id": entry.reviewer_id,
                     "note": entry.note, "created_at": entry.created_at.isoformat()}
                    for entry in document.classification_feedback.all().order_by("-created_at", "-id")],
    }


@transaction.atomic
def submit_feedback(document, reviewer, data):
    # Serialize decisions for the same document, including SQLite's write-lock behavior.
    from .models import Document
    Document.objects.select_for_update().get(pk=document.pk)
    if ProcessingJob.objects.filter(document=document, state__in=["queued", "running"]).exists():
        raise ValidationError({"detail": "Wait for document extraction to finish."})
    prediction = DocumentClassification.objects.filter(document=document).first()
    if prediction is None:
        raise ValidationError({"detail": "Classify the document before submitting feedback."})
    if not isinstance(data, dict):
        raise ValidationError({"detail": "Expected an object."})
    if set(data) - {"action", "category", "note"}:
        raise ValidationError({"detail": "Unexpected feedback fields."})
    action = data.get("action")
    category = data.get("category", "")
    note = data.get("note", "")
    if action not in ACTIONS or not isinstance(note, str) or len(note) > 1000:
        raise ValidationError({"detail": "Invalid action or note (maximum 1000 characters)."})
    if action == "verify":
        if category not in ("", prediction.category):
            raise ValidationError({"detail": "Verification must agree with the current machine category."})
        category = prediction.category
    elif action == "override":
        if category not in CATEGORIES or category == prediction.category:
            raise ValidationError({"detail": "Select a different valid category for override."})
        if not note.strip():
            raise ValidationError({"detail": "Explain the category override."})
    else:
        if category not in ("", None):
            raise ValidationError({"detail": "Clearing a review does not accept a category."})
        category = ""
    ClassificationFeedback.objects.create(
        document=document, reviewer=reviewer, action=action, category=category,
        machine_category=prediction.category, note=note.strip(),
    )
    return feedback_payload(document)


def feedback_summary(documents):
    """Evaluation of actual decisions, not independent test accuracy."""
    ids = list(documents.values_list("pk", flat=True))
    decisions = ClassificationFeedback.objects.filter(document_id__in=ids).order_by("document_id", "-created_at", "-id")
    latest = {}
    for decision in decisions:
        latest.setdefault(decision.document_id, decision)
    counts = {"verified": 0, "overridden": 0, "cleared": 0, "unreviewed": len(ids)}
    by_category = {category: {"verified": 0, "overridden": 0} for category in sorted(CATEGORIES)}
    for decision in latest.values():
        if decision.action == "clear":
            counts["cleared"] += 1
            continue
        counts["unreviewed"] -= 1
        kind = "verified" if decision.action == "verify" else "overridden"
        counts[kind] += 1
        by_category[decision.category][kind] += 1
    return {"basis": "owner_review_feedback_not_independent_accuracy", "document_count": len(ids),
            "counts": counts, "by_human_category": by_category}
