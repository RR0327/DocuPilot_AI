# DocuPilot AI — presenter notes and demonstration cues

**Owner:** Tech_Innovators · **Database:** SQLite3 only · **Audience:** project judges/reviewers

## Recommended 10-minute run of show

| Time | Demo action | Presenter statement | Fallback |
|---|---|---|---|
| 0:00–1:30 | Title and login | This is a private, owner-scoped document analysis app using Django sessions and CSRF. | Show redacted login evidence |
| 1:30–3:45 | Upload PDF/TXT, extract and ask | Retrieved answers carry document and page references. | Use a pre-extracted consented TXT |
| 3:45–6:15 | Invoice extraction and correction | Arithmetic checks do not replace accountant approval. | Use a prepared sample invoice |
| 6:15–8:00 | Classifier evidence and override | Rule-based signals allow `unknown` and retain machine versus human decisions. | Use a prepared classified case |
| 8:00–9:00 | Two-account private access | Owner B cannot read Owner A's documents or private PDF. | Show redacted API test output |
| 9:00–10:00 | Acceptance report and backup verification | SQLite3 snapshot and checksum checks; production is not yet certified. | Show previously produced, redacted reports |

## Setup
1. Use **only synthetic or consented demo files**. Prepare two test users, one text PDF/TXT and one invoice.
2. From `backend/`: run `python manage.py check`, `python manage.py test`, `python manage.py release_acceptance`, and `python manage.py runserver`.
3. From `frontend/`: run `npm install`, `npm test`, `npm run build`, `npm run dev`.
4. If optional Celery/Redis is disabled, use synchronous extraction. If embeddings are unavailable, use keyword retrieval.
5. Hide passwords, `.env`, database contents and unredacted private documents.

## Questions to anticipate
- **Why SQLite3?** Local-first, simple demo; write concurrency limits constrain scale.
- **Does it generate LLM answers?** No; retrieval is grounded in indexed chunks, optional semantic E5.
- **Is 100% synthetic classification accuracy real-world accuracy?** No. Independent adjudication is required.
- **Is this production-ready?** The submission is prepared for controlled demo. Internet-facing production has unresolved security and operations gates.
- **Are backups encrypted?** No. The utility verifies hashes and SQLite integrity; operators must encrypt off-site backups.

## File change in this handoff
User-supplied `scripts/backup_restore.py` is incorporated unchanged. Its archive-verification SQLite temporary-file handling now uses `NamedTemporaryFile(delete=False)` and explicit cleanup, improving Windows compatibility.
