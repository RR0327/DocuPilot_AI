# Contributing to DocuPilot AI

Thank you for your interest in contributing. DocuPilot AI is maintained by **Tech_Innovators** and released under the [MIT License](LICENSE).

## Before starting

1. Search existing issues and pull requests to avoid duplication.
2. For a substantial feature or architectural change, open an issue describing the intended scope and acceptance criteria.
3. Follow the project's current phase and avoid introducing unreviewed dependencies or breaking existing functionality.

## Local development

Follow the [Windows 11 setup instructions](README.md#getting-started-on-windows-11). Before opening a pull request, run:

```powershell
# From repository root, in an activated Python virtual environment
cd backend
python manage.py check
python manage.py test
cd ..\frontend
npm install
npm run build
```

When your change introduces new behavior, add corresponding unit, integration, or regression tests. Clearly document any test you cannot run.

## Pull request expectations

- Keep changes focused, descriptive, and consistent with the existing structure.
- Explain the problem, approach, API or schema impact, and verification results.
- Include complete migration files for model/schema changes.
- Never include real invoices, customer records, passwords, API keys, `.env`, or production documents.
- Preserve license notices in source or redistributed files where applicable.
- Expect review before merge; submitting a pull request does not guarantee acceptance.

## Security issues

**Do not disclose exploitable vulnerabilities in public issues.** Read [SECURITY.md](SECURITY.md) for private reporting guidance.

## Licensing and attribution

By submitting a contribution, you agree to license your submitted work under this project's MIT License and affirm you have the necessary rights to contribute it. You retain copyright in your contributions unless another written agreement states otherwise. **Tech_Innovators** retains copyright in its own original contributions. Do not add unrelated proprietary or incompatible-licensed code.

For project questions or proposed enhancements, use GitHub Issues or Discussions after those features are enabled by the repository maintainers.
