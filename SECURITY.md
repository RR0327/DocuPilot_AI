# Security Policy

DocuPilot AI is maintained by **Tech_Innovators**. This release is intended
for controlled demonstration, internal evaluation, and review. **Public
Internet production deployment has not been independently approved.**

For the system’s trust boundaries and runtime data flows, see
[Architecture and System Design](handoff/ARCHITECTURE_AND_SYSTEM_DESIGN.md).

## Supported release

| Release | Status |
| --- | --- |
| Current demonstration release | Security fixes and regression reports are accepted for controlled demonstration; there is no production support guarantee. |

## Implemented security controls

- Django session authentication with CSRF protection, secure production
  cookies, session rotation, idle expiry, password validation, and login
  failure throttling.
- HTTP Basic authentication is disabled by default. Any development opt-in
  requires `DEBUG=true` and the explicit development setting.
- Authenticated APIs use owner-scoped access controls for documents, extracted
  invoices, PDF evidence, classifications, reviews, exports, and processing
  jobs.
- Uploaded documents are stored in private storage without a public media URL.
  Private PDF access is served through an authenticated, owner-scoped route.
- Production configuration checks reject the development secret key and
  require a sufficiently long secret. HTTPS, secure cookies, allowed hosts,
  CSRF trusted origins, and reverse-proxy trust must be configured for the
  deployment.
- Backup verification includes SQLite integrity checks and SHA-256 checksums.
  Restore is dry-run by default, confirmation-gated, and refuses to overwrite
  an existing data location.
- Automated tests cover authentication, authorization, private media
  exposure, release configuration, and backup/restore behavior.

These controls do not replace infrastructure hardening, network protection,
monitoring, incident response, a deployment-specific threat model, or an
independent security assessment.

## Privacy and data-handling requirements

- Use synthetic or properly authorized documents in demonstrations and tests.
  Do not upload regulated or confidential production data until the required
  approvals and controls are complete.
- Treat `backend/db.sqlite3`, `backend/private_media/`, exports, logs, and
  backup archives as sensitive data.
- Never commit or publish `.env` files, credentials, databases, private media,
  backup archives, or document excerpts.
- The backup utility does **not** encrypt archives. Encrypt backups before
  off-site storage and restrict access to the archives and encryption keys.
- Define retention, deletion, access-review, incident-response, and
  data-subject procedures for the intended deployment. The application does
  not provide a complete organizational privacy program.
- Do not expose Django’s development server directly to the Internet. Only
  trust forwarded HTTPS headers from a reverse proxy controlled by the
  operator.

## Known security and operational limitations

- The default deployment uses one SQLite database and local private storage.
  It is intended for modest load and is not a horizontally scalable or highly
  available deployment. SQLite concurrent-writer constraints apply when
  optional Celery/Redis processing is enabled.
- Application throttling does not prevent distributed denial-of-service
  attacks. Add network-level rate limiting, monitoring, alerting, and
  incident-response procedures.
- Administrator MFA, enterprise identity integration, centralized audit
  logging, and independent penetration testing are not complete features of
  this release.
- OCR depends on the local Tesseract installation and may produce incorrect
  or incomplete text. PDF evidence highlighting is approximate text-layer
  matching, not guaranteed geometric provenance.
- Semantic and hybrid search depend on an optional local embedding model.
  Keyword search is the fallback; semantic modes may be unavailable when the
  model or offline cache is missing.
- Invoice extraction, arithmetic checks, and deterministic classification are
  decision-support features. They can fail on unfamiliar layouts, ambiguous
  documents, or poor OCR output and require human verification before
  consequential decisions.
- Synthetic evaluation fixtures and owner feedback are not independent
  evidence of real-world accuracy, fairness, or regulatory suitability.
- Answers are extractive and evidence-linked; this release does not provide
  general-purpose LLM generation or a guarantee of complete or correct
  answers.

## Production prerequisites

Before external deployment or use with sensitive data:

1. Use a supported production application server behind a correctly
   configured HTTPS reverse proxy.
2. Set a unique secret, restricted allowed hosts, trusted CSRF origins, secure
   cookie/proxy settings, and disable all development overrides.
3. Add network controls, centralized logging, monitoring, alerting, patch
   management, and incident response.
4. Encrypt and access-control backups, test restoration, and define retention
   and deletion procedures.
5. Complete a deployment-specific threat model and independent security
   assessment, including penetration testing where appropriate.
6. Validate extraction, OCR, classification, and search quality on
   representative authorized data, with human review for consequential use.

Until these prerequisites are satisfied, describe DocuPilot AI as a
controlled demonstration or internal evaluation tool, not a production
service.

## Reporting a vulnerability

**Do not post exploit details, credentials, or confidential documents in a
public issue.**

1. Use the repository’s **Security → Report a vulnerability** option if
   private reporting is enabled.
2. Otherwise request a private contact channel from a project maintainer
   without publishing vulnerability details.
3. Include the affected revision, impact, reproducible steps, and suggested
   mitigation. Use synthetic examples and omit real credentials or customer
   data.

No dedicated security reporting email or response-time guarantee is currently
published.
