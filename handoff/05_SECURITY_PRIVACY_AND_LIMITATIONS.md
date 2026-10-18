# Security, privacy and reliability statements

## Implemented safeguards (verify in your deployment)
- Django session authentication, CSRF-protected writes, HTTP-only cookies; Secure cookie flags and HTTPS redirect when non-debug; session rotation and idle expiry.
- SQLite-backed login failure throttling, default five attempts/15 minutes; development-only opt-in Basic support explicitly disabled in production.
- Owner-isolated document metadata, private PDF download, invoice records, review, processing jobs and classification endpoints; anonymous and cross-owner regression tests.
- No public MEDIA_URL for private uploads. Operational feedback export excludes source text, titles, notes, reviewer identities and internal identifiers.
- SQLite snapshot backup with SHA-256, checksum verification, integrity checks, path validation and restore overwrite refusal.

## Known limitations and no-go conditions
1. **Production deployment is not certified.** Independent penetration testing, live TLS and proxy review, operational monitoring, incident response and secure recovery drill remain site-specific work.
2. **Rate limiting is application-level.** It cannot replace edge throttling, DDoS controls, abuse telemetry and monitoring. IPv4/IPv6 source address correctness depends on trusted network configuration.
3. **No MFA:** privileged accounts are not protected by a second factor; strengthen administrator access before external deployment.
4. **Backups are confidential but unencrypted by the utility.** Encrypt and restrict backups, retain offline copies, verify restoration and test retention/deletion procedures.
5. **SQLite:** suitable for local/small deployments, but write serialization and backup/media consistency require controlled concurrency and paused uploads/workers for a coherent snapshot.
6. **Classification:** deterministic rules; `unknown` abstention and explainable excerpts. Synthetic metrics and operational reviewer agreement are **not** independently validated real-world accuracy. Genuine evaluation requires consented source documents and adjudicated labels.
7. **Retrieval/OCR:** OCR can mistranscribe; semantic model availability is optional; retrieval is extractive, not LLM generation. Citations and geometric PDF highlighting need human checking.
8. **Invoice intelligence:** extraction and arithmetic checks are not an accounting audit, settled-payment verification, tax opinion, or substitute for original documents and human approval.
9. **Dependencies / privacy:** model downloads may involve third-party infrastructure on first install. Keep offline model mode and asset access aligned with the data policy.
10. **Public demos:** use fabricated/consented sample files and minimal access. Never demo private real user documents on a public host.

## Data lifecycle and threat model
Data at rest: SQLite3 application state, private originals, optional local model cache. Data in transit: TLS required externally. Threats: stolen sessions, credential stuffing, document ID enumeration, malicious PDF uploads, content extraction leaks, poisoned classification feedback, backup theft, and worker concurrency errors. Controls must be validated with explicit owner A/B requests and archive recovery rehearsal. Consult `../SECURITY.md` for disclosure instructions.

## Release decision
**Local demonstration:** acceptable only with the user-reported acceptance records retained and no sensitive real files. **Public Internet production:** **NO-GO** until independent security review, HTTPS deployment checks, secrets handling, validated backups, monitoring, MFA decisions and real data governance are completed.
