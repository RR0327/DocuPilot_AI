# Security Policy

DocuPilot AI is maintained by **Tech_Innovators**. The completed project is intended for controlled demonstration and review. **Public Internet production deployment has not been independently approved.**

## Supported Release

| Release                                 | Status                                                                                                       |
| --------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| Final hackathon / demonstration release | Security fixes and regression reports accepted for controlled demonstration; no production support guarantee |

## Implemented Security Controls

- Django session authentication with CSRF protection, session rotation, idle expiry, and login failure throttling.
- HTTP Basic authentication disabled by default; any development opt-in requires `DEBUG=true`.
- Owner-scoped document, invoice, PDF evidence, classification, review and processing APIs.
- Private file storage without a public uploaded-document URL.
- Production configuration checks for secure cookies, HTTPS settings and deployment secrets.
- Backup verification through SHA-256 checksums and SQLite integrity checks; restore requires explicit confirmation and refuses overwrite of existing data.
- Automated authentication, authorization, backup and release checks.

## Reporting a Vulnerability

**Do not post exploit details or confidential documents in public GitHub issues.**

1. Use the repository's **Security → Report a vulnerability** option if private reporting is enabled.
2. Otherwise request a private contact channel from a project maintainer without publishing vulnerability details.
3. Supply the affected revision, impact, reproducible steps, and suggested mitigation, without real credentials or customer data.

No dedicated security reporting email or response-time guarantee is currently published.

## Production and Privacy Limitations

- Use HTTPS, a production application server, a unique secret key, restricted allowed hosts, and a correctly configured trusted reverse proxy before external deployment.
- Add edge/network-level rate limiting, monitoring, and deployment-specific security assessments; application throttling alone does not prevent distributed attacks.
- Administrator MFA and external penetration testing are not included in the current release.
- Do not publish `.env`, SQLite databases, private media, backup ZIPs, or sensitive document excerpts.
- Backup archives **are not encrypted** by the utility; encrypt and restrict access before off-site storage.
- Classification uses explainable heuristic rules. Synthetic evaluation and owner feedback do not establish independent real-world accuracy; financial extraction requires human verification.
- Only upload synthetic or properly authorized documents to demonstration environments. Avoid regulated or confidential production data until required controls and approval are completed.
