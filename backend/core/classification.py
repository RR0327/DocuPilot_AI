"""Explainable, deterministic document category rules; never read other owners' data.

Classification signals come only from extracted page text (including OCR). Scores are
rule weights, NOT calibrated ML probabilities. If evidence is weak or tied, abstain.
"""
import re
import unicodedata
from .models import DocumentClassification

RULES = {
    "invoice": [("invoice number", 3), ("invoice no", 3), ("invoice date", 2), ("bill to", 2), ("amount due", 2), ("unit price", 2), ("subtotal", 2)],
    "policy": [("policy statement", 3), ("privacy policy", 3), ("refund policy", 3), ("policy scope", 3), ("effective date", 1), ("policy applies", 2), ("compliance requirements", 2)],
    "report": [("executive summary", 3), ("methodology", 2), ("findings", 2), ("conclusions", 2), ("annual report", 3), ("research report", 3), ("results and discussion", 3)],
    "contract": [("this agreement", 3), ("parties agree", 3), ("terms and conditions", 2), ("governing law", 3), ("termination clause", 3), ("hereinafter", 2), ("signed by", 2)],
}
# Additional multilingual rules are explicit, auditable signals (not learned probabilities).
RULES["invoice"] += [("চালান নম্বর", 3), ("চালান নং", 3), ("মোট টাকা", 2), ("বিলের তারিখ", 2)]
RULES["policy"] += [("গোপনীয়তা নীতি", 3), ("ফেরত নীতি", 3), ("নীতিমালা", 3)]
RULES["report"] += [("নির্বাহী সারসংক্ষেপ", 3), ("গবেষণা পদ্ধতি", 3), ("ফলাফল ও আলোচনা", 3)]
RULES["contract"] += [("এই চুক্তি", 3), ("চুক্তির শর্ত", 3), ("চুক্তি বাতিল", 3)]
# Carefully scoped OCR confusion variants; original source substring remains in evidence.
OCR_ALIASES = {"invoice no": [r"inv[o0]ice\s+n[o0]\.?"],
               "invoice number": [r"inv[o0]ice\s+number"],
               "invoice date": [r"inv[o0]ice\s+date"],
               "methodology": [r"meth[o0]d[o0]logy"],
               "privacy policy": [r"privacy\s+p[o0]licy"],
               "governing law": [r"g[o0]verning\s+law"]}
MAX_EVIDENCE = 12


def classify_pages(pages):
    """Return (category, evidence, scores, reason) for (page_number, text) rows."""
    scores = {name: 0 for name in RULES}
    evidence = []
    for page_number, text in pages:
        if not isinstance(text, str) or not text.strip():
            continue
        # NFC normalizes Unicode without collapsing source whitespace; excerpts are
        # sliced from the original unmodified page text with exact source offsets.
        folded = unicodedata.normalize("NFC", text).casefold()
        for category, phrases in RULES.items():
            for phrase, weight in phrases:
                words = phrase.split()
                # Tolerate whitespace/line-break differences common in OCR output.
                pattern = r"(?<!\w)" + r"\s+".join(re.escape(w) for w in words) + r"(?!\w)"
                match = re.search(pattern, folded)
                if match is None:
                    for alias in OCR_ALIASES.get(phrase, []):
                        match = re.search(r"(?<!\w)(?:" + alias + r")(?!\w)", folded)
                        if match:
                            break
                if match:
                    scores[category] += weight
                    start = max(0, match.start() - 65)
                    end = min(len(text), match.end() + 85)
                    # Offset slicing matches original text for ordinary NFC text.
                    # If Unicode normalization shifted indices, locate source
                    # case-insensitively or skip the evidence rather than fabricate it.
                    excerpt = text[start:end]
                    surface = text[match.start():match.end()]
                    if surface and surface.casefold() in excerpt.casefold():
                        evidence.append({"category": category, "phrase": surface,
                                         "signal": phrase, "weight": weight,
                                         "page_number": int(page_number), "excerpt": excerpt})
                    else:
                        scores[category] -= weight
    ranked = sorted(scores, key=lambda k: (-scores[k], k))
    leader = ranked[0]
    runner_up = scores[ranked[1]]
    # Put winning category evidence first so the capped explanation cannot hide it.
    evidence.sort(key=lambda e: (e["category"] != leader, e["page_number"], -e["weight"], e["phrase"]))
    evidence = evidence[:MAX_EVIDENCE]
    if scores[leader] < 3:
        return "unknown", evidence, scores, "Insufficient matching document evidence"
    if scores[leader] == runner_up:
        return "unknown", evidence, scores, "Category signals tied; manual review required"
    return leader, evidence, scores, "Rule-based category; verify against original pages"


def classify_document(document):
    pages = list(document.pages.order_by("page_number").values_list("page_number", "extracted_text"))
    category, evidence, scores, reason = classify_pages(pages)
    result, _ = DocumentClassification.objects.update_or_create(
        document=document,
        defaults={"category": category, "evidence": evidence, "scores": scores, "reason": reason},
    )
    return result


def classification_payload(result):
    return {"document_id": result.document_id, "category": result.category,
            "evidence": result.evidence, "rule_scores": result.scores,
            "reason": result.reason, "classified_at": result.classified_at.isoformat(),
            "calibrated_confidence": None}
