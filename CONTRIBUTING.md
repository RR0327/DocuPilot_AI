# Contributing to DocuPilot AI

DocuPilot AI is maintained by **Tech_Innovators**. Contributions are welcome through GitHub issues and pull requests.

## Before You Contribute

- Search existing issues and pull requests before proposing a change.
- For substantial changes, describe the problem, solution, and acceptance criteria in an issue first.
- Preserve SQLite3, document-owner authorization, source evidence, and all existing application workflows unless an agreed change requires otherwise.
- Avoid unreviewed dependencies, breaking API changes, and incompatible-licensed code.

## Development and Testing

Follow the [Windows 11 setup](README.md#getting-started-windows-11) in the README. Run the relevant tests before opening a pull request:

```powershell
# From backend/
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test --verbosity 2

# From frontend/
npm test
npm run build
npm run test:e2e

# From repository root
python -m unittest discover -s scripts -p "test_*.py" -v
```

Include tests for new functionality. Document any test that could not be executed and why.

## Pull Requests

- Keep changes focused and explain the behavior, implementation, and verification results.
- Include Django migration files when changing persisted models.
- Retain private-document ownership checks and CSRF/session protection for affected endpoints.
- Do not commit `.env`, credentials, populated SQLite3 databases, uploaded documents, backups, or genuine confidential evaluation data.
- Review is required before merging.

## Security and Licensing

Report security weaknesses **privately** as described in [SECURITY.md](SECURITY.md), not in public issues.

By contributing, you confirm you have rights to the submitted work and agree that it may be distributed under the project's [MIT License](LICENSE). **Tech_Innovators** retains ownership of its original contributions.
