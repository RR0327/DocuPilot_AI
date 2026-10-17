# Security Policy

DocuPilot AI is maintained by **Tech_Innovators**.

## Supported versions

| Version | Security support |
| --- | --- |
| Phase 0 development starter (0.x) | Development only; no production security support guarantee |
| Future production releases | Policy will be updated when a supported release is published |

**Do not use the current starter to process private, confidential, or regulated documents.** Upload authorization, file isolation, threat controls, and production hardening are not yet implemented.

## Reporting a vulnerability

Please report security vulnerabilities **privately**, not in public issues or pull requests.

1. Open the repository's **Security** tab and use **Report a vulnerability** if private vulnerability reporting has been enabled.
2. If that option is unavailable, contact the repository maintainer through an established private channel and request a secure reporting method. Do not post exploit details publicly.
3. Include an affected version or commit, impact, reproduction steps, and suggested mitigations if available. Remove real credentials and sensitive customer content.

No private reporting email address has been designated yet; none is claimed in this policy.

## Scope and response

Maintainers will triage credible reports when received; specific response or remediation deadlines are **not promised** at this stage. Please allow time for coordinated disclosure and a fix before public publication.

## Security requirements for future releases

Planned controls include:

- Enforced authentication and document-level authorization.
- Server-side file type/size validation and safe storage.
- Separation of sensitive documents and prevention of unauthorized cross-user retrieval.
- Safe handling of environment secrets and third-party API credentials.
- Audit logging and regression tests for access controls.
- Evidence-linked answers that avoid returning information from inaccessible documents.

These are goals, **not assertions that the current version is secure**.
