"""Independent two-reviewer adjudication. This is NOT operational owner feedback.

No private documents or identifiers are sent through HTTP. The command reads local
operator-provided files only and never writes document data into the DB.
"""
import json
from collections import Counter
from pathlib import Path
from .classification_evaluation import LABELS, evaluate_cases

REQUIRED_PROVENANCE = ('source_description', 'license_or_consent', 'reviewer_protocol', 'adjudicator_protocol', 'collection_date')


def validate_adjudicated_dataset(payload):
    if not isinstance(payload, dict) or payload.get('dataset_type') != 'independently_adjudicated_documents':
        raise ValueError('Expected dataset_type=independently_adjudicated_documents')
    prov = payload.get('provenance')
    if not isinstance(prov, dict) or any(not isinstance(prov.get(k), str) or not prov[k].strip() for k in REQUIRED_PROVENANCE):
        raise ValueError('Missing independent dataset provenance, consent/license or adjudication protocol')
    if not isinstance(payload.get('cases'), list) or not payload['cases']:
        raise ValueError('At least one case required')
    validated, disagreements = [], []
    ids = set()
    for row in payload['cases']:
        if not isinstance(row, dict) or not isinstance(row.get('id'), str) or not row['id'].strip() or row['id'] in ids:
            raise ValueError('Each case must have a unique nonempty id')
        ids.add(row['id'])
        a, b, final = row.get('reviewer_a'), row.get('reviewer_b'), row.get('adjudicated_label')
        if any(label not in LABELS for label in (a,b,final)):
            raise ValueError('Reviewer and adjudicated labels must be among supported categories')
        if a != b:
            if not isinstance(row.get('adjudication_reason'), str) or len(row['adjudication_reason'].strip()) < 10:
                raise ValueError('Disagreements require a substantive adjudication reason')
            disagreements.append({'id':row['id'],'reviewer_a':a,'reviewer_b':b,'adjudicated_label':final})
        if not isinstance(row.get('pages'),list) or not row['pages']:
            raise ValueError('Each case needs source pages')
        validated.append({'id':row['id'],'label':final,'pages':row['pages']})
    return validated, disagreements, prov


def evaluate_adjudicated(payload, include_case_details=False):
    cases, disagreements, provenance = validate_adjudicated_dataset(payload)
    # Reuse the production classifier and page-grounding validator.
    result = evaluate_cases(cases, dataset_type='independently_adjudicated_documents',
                            provenance={key:provenance[key] for key in REQUIRED_PROVENANCE})
    total=len(cases)
    result['adjudication']={
        'independent_reviewer_disagreement_count':len(disagreements),
        'independent_reviewer_agreement_rate':round((total-len(disagreements))/total,4),
        'adjudicated_count':total,
        'procedure_declared_not_verified':True,
    }
    result['release_gate']={
        'status':'evaluation_only_not_production_approval',
        'independent_corpus_present':True,
        'evidence_grounded':result['evidence_issue_count']==0,
        'warning':'A small or self-selected evaluation sample cannot establish production accuracy.'
    }
    if not include_case_details:
        # Default output omits per-case text and identifiers for privacy.
        result.pop('cases',None)
    return result


def evaluate_adjudicated_path(path, include_case_details=False):
    return evaluate_adjudicated(json.loads(Path(path).read_text(encoding='utf-8')), include_case_details)
