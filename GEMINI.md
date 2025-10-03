# Project Standards

This document outlines the standards and conventions used in this project.

## Gemini Instructions

- Every time a structural change occurs in the project, this file must be updated to reflect the new structure.
- Never create tests for the app.
- Never try to run the app through the Gemini console.

## Continuous Integration and Deployment (CI/CD)

- **CI Provider:** GitHub Actions
- **Workflow:** The CI workflow is defined in `.github/workflows/main.yml`.
- **Triggers:** The workflow is triggered on push and pull requests to the `main` branch.
- **Jobs:**
  - `build`: Runs on `ubuntu-latest` with Python 3.8.
    - Installs dependencies from `requirements.txt`.
    - Runs tests using `pytest`.

## Testing

- **Framework:** `pytest`
- **Configuration:** `pytest.ini`
- **Test Location:** `tests/`
- **File Naming Convention:** `test_*.py`

## Dependencies

- **Production:** `requirements.txt`
- **Development:** `requirements-dev.txt`

## Versioning

- A `VERSION` file in the root directory tracks the project's version.
- The version is used for Docker image tagging and releases.

## Code Style

- **General:** Follows PEP 8 guidelines.
- **Typing:** Uses type hints (e.g., `List`, `str`).
- **Modules:** Each directory contains an `__init__.py` file.
- **Logging:** Uses the `logging` module. A custom logger is configured in `src/wallbot/utils/logger.py`.
- **Database:** Uses `sqlite3`. The database helper is located in `src/wallbot/database/db_helper.py`.
- **Concurrency:** Uses the `threading` module for background tasks.

## Project Structure

The project follows the structure outlined in the `README.md` file.

```
wallbot/
├── __main__.py
├── .env.example
├── .gitignore
├── changelog
├── channel info.json
├── dev.notes.txt
├── Dockerfile
├── GEMINI.md
├── LICENSE
├── notenv copy
├── objects.txt
├── pytest.ini
├── README.md
├── requests.txt
├── requirements-dev.txt
├── requirements.txt
├── run_web.bat
├── run_web.sh
├── run.bat
├── run.sh
├── sqlite3_instructions.txt
├── start.sh
├── VERSION
├── .git/
├── .github/
│   └── workflows/
│       ├── docker-release.yml
│       └── main.yml
├── .ruff_cache/
├── data/
├── logs/
├── src/
│   ├── __init__.py
│   └── wallbot/
│       ├── __init__.py
│       ├── __main__.py
│       ├── main.py
│       ├── config/
│       │   ├── __init__.py
│       │   ├── constants.py
│       │   └── settings.py
│       ├── database/
│       │   ├── __init__.py
│       │   ├── db_helper.py
│       │   └── models.py
│       ├── telegram/
│       │   ├── __init__.py
│       │   ├── bot.py
│       │   ├── handlers.py
│       │   └── notifications.py
│       ├── utils/
│       │   ├── __init__.py
│       │   ├── logger.py
│       │   └── version.py
│       ├── wallapop/
│       │   ├── __init__.py
│       │   ├── api_client.py
│       │   ├── api_models.py
│       │   ├── categories.py
│       │   ├── monitor.py
│       │   └── search_monitor.py
│       └── web/
│           ├── app.py
│           └── templates/
│               ├── index.html
│               ├── manual_search.html
│               ├── saved_items_list.html
│               ├── saved_searches.html
│               └── searches.html
├── tests/
│   ├── __init__.py
│   └── test_version.py
└── venv/
```