# DocuPilot AI — 8–10 minute competition demonstration

**Pre-demo (not on screen):** Launch Django and React; use only consented synthetic files. Prepare two non-privileged demo accounts, a clear-text PDF/TXT containing a policy, and a simple invoice with quantity/unit price/total. Optional scanned PDF requires Tesseract; optional semantic model should be cached. Turn off desktop notifications, protect passwords, and avoid showing `.env`, local DB or confidential PDFs.

| Time | On-screen action | What to say / prove |
|---|---|---|
| 0:00–0:45 | Show project title, Tech_Innovators copyright and MIT files | 'DocuPilot AI turns private documents into searchable, cited information.' |
| 0:45–1:30 | Sign in with session login | State CSRF, idle timeout, HTTP-only cookie and rate-limited authentication; do not show password. |
| 1:30–2:45 | Upload a PDF and extract pages | Show page count and text. Explain Tesseract fallback for scanned files. |
| 2:45–3:45 | Ask a question and open source evidence | Demonstrate keyword and (if installed) semantic/hybrid mode; show page and private PDF, not a fabricated answer. |
| 3:45–5:15 | Upload an invoice, extract line items, inspect arithmetic | Distinguish extracted values from human-confirmed financial data. |
| 5:15–6:15 | Approve or correct an invoice; show supplier analytics | Human review is auditable; analytics are grouped by currency and invoice dates. |
| 6:15–7:15 | Show automatic document category and source evidence; override | Unknown class is a safe abstention; human review does not overwrite machine evidence. |
| 7:15–8:00 | Show classification quality, feedback, reliability pages | Synthetic fixture and operational agreement are not real-world accuracy. |
| 8:00–9:00 | Open second account or show prepared redacted security test evidence | Demonstrate owner A's document cannot be accessed by owner B. |
| 9:00–10:00 | Show acceptance report and verified backup process | State SQLite3-only system and honest production-readiness limits. |

**Fallbacks:** If Redis is unavailable, use synchronous extraction; if E5 model cache is missing, use keyword retrieval; if OCR language pack missing, use text PDF/TXT. If a real-data evaluation set is unavailable, explicitly disclose independent accuracy remains unmeasured.

**Closing line:** 'The project demonstrates a complete, explainable, locally deployable document intelligence workflow with user-controlled verification, while preserving explicit limits on model quality and public production security.'
