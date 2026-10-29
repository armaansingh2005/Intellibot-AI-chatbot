# Contributing

Thank you for taking the time to improve IntelliBot AI. Contributions should keep the project educational, reproducible, and honest about its limitations.

## Before you start

- Check existing issues and documentation to avoid duplicate work.
- For a significant change, open an issue first to agree on scope.
- Do not include real customer conversations, personal data, credentials, `.env` files, SQLite databases, or generated model artifacts.
- Keep sample business policies clearly labeled as illustrative.

## Local development

1. Follow the [README installation instructions](README.md#6-installation-and-environment).
2. Activate the virtual environment and make the change on a descriptive branch.
3. Run the tests and syntax check:

   ```text
   python -m pytest -q
   python -m compileall -q app.py chatbot routes models tests
   ```

4. If you change intent examples or classifier behavior, run `python scripts/train_model.py` and describe the observed metrics and dataset limitations. Do not commit the generated model.
5. Update user-facing documentation when behavior, configuration, or setup changes.

## Pull requests

- Keep changes focused and explain the problem and solution.
- Include tests for behavior changes.
- Report the commands you ran and their actual results.
- Call out security, privacy, migration, and compatibility effects.
- Use screenshots only for genuine UI changes, with private data removed.

By submitting a contribution, you confirm that you have the right to submit it. No license to use or distribute this project is granted by this guide; see [License](README.md#22-license).
