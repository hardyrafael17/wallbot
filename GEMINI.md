# Project Standards

This document outlines the standards and conventions used in this project.

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
wallapop_bot/
├── __init__.py
├── main.py
├── config/
│   ├── __init__.py
│   ├── settings.py
│   └── constants.py
├── database/
│   ├── __init__.py
│   ├── db_helper.py
│   ├── models.py
│   └── migrations.py
├── telegram/
│   ├── __init__.py
│   ├── bot.py
│   ├── handlers.py
│   └── notifications.py
├── wallapop/
│   ├── __init__.py
│   ├── api_client.py
│   ├── api_models.py
│   └── monitor.py
├── utils/
│   ├── __init__.py
│   ├── logger.py
│   ├── currency.py
│   └── exceptions.py
└── requirements.txt
```
