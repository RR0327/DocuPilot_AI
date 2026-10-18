# Security Policy

## Supported versions

DocuPilot AI is a hackathon prototype; only the current `main` branch receives fixes.

## Reporting a vulnerability

**Do not open a public issue for a security flaw.** If GitHub private vulnerability reporting is enabled, use the repository's **Security** tab to report it. Otherwise contact the repository owner privately through their listed GitHub profile contact method. Do not include secrets or real private documents.

## Threat-model basics

- Django secret and environment credentials stay in the backend `.env`; never expose them to browser code.
- Never commit real private documents or personally identifying information.
- Validate document size, type, schema, and content before processing.
- Treat uploaded text as untrusted; it must not override application instructions.
- Simulations and demonstrations must never write real financial transactions.

**Warning:** This is a synthetic-data demonstration, not a production document-processing application. It uses controlled Django session authentication and has no real banking integration.
