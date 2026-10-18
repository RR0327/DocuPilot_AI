"""Offline deterministic classification benchmark and evidence integrity validation.

Synthetic examples are for regression checks, NOT representative production accuracy.
"""
import json
import re
from pathlib import Path
from .classification import RULES, classify_pages

LABELS = (*RULES.keys(), "unknown")
FIXTURE_PATH = Path(__file__).resolve().parent.parent / "evaluation" / "classification_cases.json"


def normalize(text):
    return re.sub(r"\s+", " ", text.casefold())


def evidence_issues(pages, evidence):
    """Return a problem per ungrounded phrase/excerpt/page; do not alter source pages."""
    page_map = {int(number): normalize(text) for number, text in pages if isinstance(text, str)}
    issues = []
    for index, item in enumerate(evidence):
        page = page_map.get(item.get("page_number"))
        excerpt = item.get("excerpt", "")
        phrase = item.get("phrase", "")
        if not isinstance(excerpt, str) or not isinstance(phrase, str) or not page or not phrase:
            issues.append({"index": index, "reason": "missing page or phrase"})
        elif normalize(excerpt) not in page or normalize(phrase) not in normalize(excerpt):
            issues.append({"index": index, "reason": "evidence not found on source page"})
    return issues


def evaluate_cases(cases):
    matrix = {label: {prediction: 0 for prediction in LABELS} for label in LABELS}
    rows = []
    for case in cases:
        truth = case['label']
        if truth not in LABELS:
            raise ValueError('Invalid reference category')
        pages = [(row['page_number'], row['text']) for row in case['pages']]
        predicted, evidence, scores, reason = classify_pages(pages)
        problems = evidence_issues(pages, evidence)
        matrix[truth][predicted] += 1
        rows.append({"id": case['id'], "expected": truth, "predicted": predicted,
                     "correct": truth == predicted, "evidence_count": len(evidence),
                     "evidence_issues": problems, "reason": reason})
    per_category = {}
    for label in LABELS:
        tp = matrix[label][label]
        fp = sum(matrix[other][label] for other in LABELS if other != label)
        fn = sum(matrix[label][other] for other in LABELS if other != label)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        per_category[label] = {"support": sum(matrix[label].values()), "precision": round(precision, 4),
                               "recall": round(recall, 4), "f1": round(f1, 4)}
    n = len(rows)
    return {"dataset_type": "synthetic_regression_fixture", "sample_count": n,
            "labels": list(LABELS), "accuracy": round(sum(r['correct'] for r in rows) / n, 4) if n else 0.0,
            "macro_precision": round(sum(v['precision'] for v in per_category.values()) / len(LABELS), 4),
            "macro_recall": round(sum(v['recall'] for v in per_category.values()) / len(LABELS), 4),
            "macro_f1": round(sum(v['f1'] for v in per_category.values()) / len(LABELS), 4),
            "per_category": per_category, "confusion_matrix": matrix,
            "evidence_issue_count": sum(len(r['evidence_issues']) for r in rows),
            "cases": rows}


def run_fixture(path=FIXTURE_PATH):
    with Path(path).open(encoding='utf-8') as handle:
        cases = json.load(handle)
    return evaluate_cases(cases)
