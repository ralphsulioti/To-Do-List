# To-Do-List

Django app in `todo_list_proj/`, managed with uv (Python pinned in `.python-version`).

## Checks

Run all of these before reporting work as done:

```bash
uv run ruff check
uv run ruff format --check
uv run python todo_list_proj/manage.py check
uv run python todo_list_proj/manage.py makemigrations --check --dry-run
uv run python todo_list_proj/manage.py test todo_list
```

The tests use Django's test runner; there's no pytest here.
