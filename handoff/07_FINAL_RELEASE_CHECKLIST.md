# Final submission and release checklist

## Submission gate (can be completed for a private/local project demo)
- [ ] Tech_Innovators attribution and exact MIT LICENSE present; CONTRIBUTING.md and SECURITY.md linked from README.
- [ ] SQLite3 is the only configured application database.
- [ ] Latest user-supplied `backend/core/test_release_acceptance.py` merged intact.
- [ ] ZIP contains source, testing guides and handoff docs; excludes `.env`, SQLite data, private files, backups, virtual env and node_modules.
- [ ] Python unit/offline tests and frontend unit tests pass; attach dated logs.
- [ ] Django migrations, backend tests, browser E2E and real two-user owner isolation pass on target Windows 11 machine.
- [ ] Upload → extraction/OCR → Q&A citation → private PDF → invoice review → classification feedback demonstrated with fabricated files.
- [ ] Backup verify and isolated restore completed; retain redacted evidence.
- [ ] Demo script rehearsed; public recording excludes credentials and private records.
- [ ] User signs/date the release evidence index and archive hash.

## Production gate (not automatically satisfied by submission)
- [ ] TLS/reverse proxy, restricted hosts, secure cookies and trusted proxy settings verified.
- [ ] `DJANGO_DEBUG=false`, secret rotation and environment segregation tested; `release_acceptance --require-production` passes.
- [ ] Production server, monitoring, alerting, log redaction and response ownership in place.
- [ ] Authentication/authorization penetration testing, session and upload abuse testing completed.
- [ ] Staff/admin MFA or compensating control approved; disaster recovery/retention plan validated.
- [ ] Independent adjudicated representative document dataset evaluated; thresholds and error budget signed off.
- [ ] Risk owner accepts residual issues listed in `05_SECURITY_PRIVACY_AND_LIMITATIONS.md`.

**Release decision:** Private/local demonstration candidate pending artifacts and operator signoff. Internet-facing production remains NO-GO until the separate production gate is complete.
